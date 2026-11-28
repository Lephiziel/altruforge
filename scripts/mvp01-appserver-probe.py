"""Exercise a Codex app-server v2 turn under the configured permission profile."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


def read_messages(stream: Any, messages: queue.Queue[dict[str, Any] | None]) -> None:
    for line in stream:
        try:
            messages.put(json.loads(line))
        except json.JSONDecodeError as error:
            raise RuntimeError("app-server emitted invalid JSON") from error
    messages.put(None)


def persist_checkpoint(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as checkpoint:
        json.dump(state, checkpoint, sort_keys=True)
        checkpoint.write("\n")
        checkpoint.flush()
        os.fsync(checkpoint.fileno())
    temporary.replace(path)
    if os.name != "nt":
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


class AppServer:
    def __init__(self, cwd: Path) -> None:
        self.process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.messages: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.reader = threading.Thread(
            target=read_messages,
            args=(self.process.stdout, self.messages),
            daemon=True,
        )
        self.reader.start()
        self.next_id = 1

    def send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(
        self, method: str, params: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timed out waiting for {method}")
            message = self.messages.get(timeout=remaining)
            if message is None:
                raise RuntimeError("app-server closed its output")
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(json.dumps(message["error"]))
                return message["result"]

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument(
        "--interrupt-on",
        type=Path,
        help="Interrupt the active turn once this workspace-relative file exists.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Atomically persist a test supervisor checkpoint outside the worker workspace.",
    )
    parser.add_argument(
        "--resume-checkpoint",
        type=Path,
        help="Start a fresh app-server and resume the thread recorded in a checkpoint.",
    )
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()

    if args.resume_checkpoint:
        if args.prompt or args.interrupt_on or args.checkpoint:
            parser.error("--resume-checkpoint cannot be combined with a new turn")
        args.resume_checkpoint = args.resume_checkpoint.resolve()
        state = json.loads(args.resume_checkpoint.read_text(encoding="utf-8"))
        cwd = Path(state["cwd"]).resolve()
        try:
            args.resume_checkpoint.relative_to(cwd)
        except ValueError:
            pass
        else:
            parser.error("--resume-checkpoint must be outside the worker workspace")
        server = AppServer(cwd)
        try:
            server.request(
                "initialize",
                {"clientInfo": {"name": "mvp01-boundary-probe", "version": "0.1.0"}},
                args.timeout,
            )
            server.request(
                "thread/resume", {"threadId": state["thread_id"]}, args.timeout
            )
            state["status"] = "resumed"
            persist_checkpoint(args.resume_checkpoint, state)
            print("thread_resume=OK")
            print("checkpoint_status=resumed")
            return 0
        finally:
            server.stop()

    if args.cwd is None or args.prompt is None:
        parser.error("--cwd and --prompt are required unless resuming a checkpoint")
    if args.interrupt_on and not args.checkpoint:
        parser.error("--interrupt-on requires --checkpoint")

    cwd = args.cwd.resolve()
    if args.checkpoint:
        args.checkpoint = args.checkpoint.resolve()
        try:
            args.checkpoint.relative_to(cwd)
        except ValueError:
            pass
        else:
            parser.error("--checkpoint must be outside the worker workspace")
    interrupt_path = None
    if args.interrupt_on:
        if args.interrupt_on.is_absolute():
            parser.error("--interrupt-on must be workspace-relative")
        interrupt_path = (cwd / args.interrupt_on).resolve()
        try:
            interrupt_path.relative_to(cwd)
        except ValueError:
            parser.error("--interrupt-on must stay inside the worker workspace")
        if interrupt_path.exists():
            parser.error("--interrupt-on marker already exists; remove stale test output")

    server = AppServer(cwd)
    try:
        server.request(
            "initialize",
            {"clientInfo": {"name": "mvp01-boundary-probe", "version": "0.1.0"}},
            args.timeout,
        )
        print("initialize=OK")
        server.send({"method": "initialized", "params": {}})
        thread = server.request(
            "thread/start", {"cwd": str(cwd), "approvalPolicy": "never"}, args.timeout
        )["thread"]
        thread_id = thread["id"]
        print("thread_id=" + thread_id)
        checkpoint_state = {
            "version": 1,
            "status": "running",
            "cwd": str(cwd),
            "thread_id": thread_id,
            "turn_id": None,
            "marker": str(args.interrupt_on) if args.interrupt_on else None,
        }
        if args.checkpoint:
            persist_checkpoint(args.checkpoint, checkpoint_state)
        turn = server.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [{"type": "text", "text": args.prompt}],
            },
            args.timeout,
        )["turn"]
        turn_id = turn["id"]
        checkpoint_state["turn_id"] = turn_id
        if args.checkpoint:
            persist_checkpoint(args.checkpoint, checkpoint_state)
        deadline = time.monotonic() + args.timeout
        interrupted = False

        while time.monotonic() < deadline:
            if interrupt_path and interrupt_path.exists() and not interrupted:
                checkpoint_state["status"] = "interrupt_requested"
                if args.checkpoint:
                    persist_checkpoint(args.checkpoint, checkpoint_state)
                server.request(
                    "turn/interrupt",
                    {"threadId": thread_id, "turnId": turn_id},
                    args.timeout,
                )
                interrupted = True
                print("interrupt=REQUESTED")

            try:
                message = server.messages.get(timeout=0.2)
            except queue.Empty:
                continue
            if message is None:
                raise RuntimeError("app-server closed its output during the turn")
            if "id" in message and "method" in message:
                raise RuntimeError(
                    "unexpected app-server request: " + str(message.get("method"))
                )
            method = message.get("method", "")
            params = message.get("params", {})
            if method == "item/completed":
                item = params.get("item", {})
                if item.get("type") == "commandExecution":
                    print("command_exit=" + str(item.get("exitCode")))
                    print(item.get("aggregatedOutput", "").strip())
                elif item.get("type") == "agentMessage":
                    print("agent_message=" + item.get("text", "").strip())
            if method == "turn/completed":
                status = params.get("turn", {}).get("status", "unknown")
                print("turn_status=" + str(status))
                if interrupted and args.checkpoint:
                    checkpoint_state["status"] = "interrupted"
                    persist_checkpoint(args.checkpoint, checkpoint_state)
                    print("checkpoint_status=interrupted")
                break
        else:
            raise TimeoutError("timed out waiting for turn completion")

        if interrupted:
            server.request("thread/resume", {"threadId": thread_id}, args.timeout)
            print("thread_resume=OK")
        return 0
    finally:
        server.stop()


if __name__ == "__main__":
    raise SystemExit(main())
