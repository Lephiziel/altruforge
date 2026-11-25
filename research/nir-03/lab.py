"""Pinned Forgejo, Git fixtures, and loopback-only HTTP for P0.1."""

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import pwd
import secrets
import socket
import subprocess
import threading
import time
from urllib.parse import urlsplit


FORGEJO_VERSION = "15.0.12+gitea-1.22.0"
FORGEJO_SHA256 = "d10b861514736e29f43e9d8e70bcf8e57a0b26e9e212412952ee4fa987662ca5"
OWNER = "publisher"
ACTOR = "contributor"
HEAD = "refs/heads/candidate"
BASE = "refs/heads/main"
TIMEOUT = 12
POLICY = {"allowed_paths": ["artifact.txt"], "contents": "verified artifact v1\n"}


def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


class Journal:
    """Retain observations before the controller advances a fault barrier."""

    def __init__(self, path):
        self.file = path.open("x", encoding="utf-8")
        self.lock = threading.Lock()
        self.started = time.monotonic_ns()
        self.sequence = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.file.close()

    def record(self, event, **fields):
        with self.lock:
            self.sequence += 1
            entry = {
                "seq": self.sequence,
                "ms": round((time.monotonic_ns() - self.started) / 1e6, 3),
                "event": event,
                **fields,
            }
            self.file.write(json.dumps(entry, sort_keys=True) + "\n")
            self.file.flush()
            os.fsync(self.file.fileno())


def request(origin, path, method="GET", payload=None, auth=None):
    url = urlsplit(origin)
    if (url.scheme, url.netloc, url.path, url.query, url.fragment) != (
        "http", f"127.0.0.1:{url.port}", "", "", ""
    ) or not url.port or not path.startswith("/") or path.startswith("//"):
        raise ValueError("expected a loopback HTTP origin and an absolute API path")
    headers = {"Accept": "application/json"}
    if auth:
        headers["Authorization"] = auth
    if payload is not None:
        headers["Content-Type"] = "application/json"
    connection = http.client.HTTPConnection("127.0.0.1", url.port, timeout=TIMEOUT)
    try:
        body = json.dumps(payload).encode() if payload is not None else None
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def api(origin, path, method="GET", payload=None, auth=None):
    status, body = request(origin, path, method, payload, auth)
    try:
        return status, json.loads(body) if body else None
    except (UnicodeError, ValueError):
        return status, {"non_json_response": body[:500].decode(errors="replace")}


def require(reply, status):
    actual, value = reply
    if actual != status:
        raise RuntimeError(f"expected HTTP {status}, received {actual}: {value!r}")
    return value


def git(*args, cwd=None, auth=None, check=True):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_NAME="NIR-03 fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="NIR-03 fixture",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
        GIT_AUTHOR_DATE="2026-11-25T00:00:00Z",
        GIT_COMMITTER_DATE="2026-11-25T00:00:00Z",
        LC_ALL="C",
    )
    if auth:
        env.update(
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="http.extraHeader",
            GIT_CONFIG_VALUE_0=f"Authorization: {auth}",
        )
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
        timeout=TIMEOUT, check=check,
    )


def ref_tips(url):
    result = git("ls-remote", "--refs", url)
    return {ref: sha for sha, ref in (line.split("\t") for line in result.stdout.splitlines())}


def git_result(result):
    return {
        "command": result.args,
        "exit": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@dataclass(frozen=True)
class Fixture:
    source: Path
    actor_source: Path
    base: str
    candidate: str
    drift_a: str
    drift_b: str
    evidence: dict

    @classmethod
    def create(cls, root):
        source = root / "source"
        git("init", "--quiet", "--template=", "--object-format=sha1", "-b", "main", str(source))

        def commit(contents, title):
            (source / "artifact.txt").write_text(contents, encoding="utf-8")
            git("add", "artifact.txt", cwd=source)
            git("commit", "--quiet", "-m", title, cwd=source)
            return git("rev-parse", "HEAD", cwd=source).stdout.strip()

        base = commit("baseline\n", "Base")
        candidate = commit(POLICY["contents"], "Verified candidate")
        git("branch", "verified", candidate, cwd=source)
        drift_a = commit("contributor change A\n", "Contributor A")
        git("switch", "--quiet", "-c", "alternate", candidate, cwd=source)
        drift_b = commit("contributor change B\n", "Contributor B")
        actor_source = root / "actor"
        git("clone", "--quiet", "--no-hardlinks", str(source), str(actor_source))

        # The verifier examines objects named by SHA and runs before any trial.
        paths = git("diff", "--name-only", base, candidate, cwd=source).stdout.splitlines()
        content = git("show", f"{candidate}:artifact.txt", cwd=source).stdout
        parent = git("rev-parse", f"{candidate}^", cwd=source).stdout.strip()
        tree = git("rev-parse", f"{candidate}^{{tree}}", cwd=source).stdout.strip()
        if paths != POLICY["allowed_paths"] or content != POLICY["contents"] or parent != base:
            raise RuntimeError("fixture verification failed")
        evidence = {
            "verifier": "p0.1 fixture object checks",
            "checks": {
                "changed_paths": paths, "contents_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "direct_parent": parent,
            },
            "result": "pass",
            "base": base,
            "candidate": candidate,
            "tree": tree,
            "policy_sha256": digest(POLICY),
        }
        return cls(source, actor_source, base, candidate, drift_a, drift_b, evidence)


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


class Lab:
    def __init__(self, binary, root, journal):
        self.binary = binary.resolve(strict=True)
        self.root = root
        self.journal = journal
        self.port = free_port()
        self.origin = f"http://127.0.0.1:{self.port}"
        self.config = root / "lab.ini"
        self.passwords = {name: secrets.token_urlsafe(24) for name in (OWNER, ACTOR)}
        self.process = None

    def auth(self, name):
        return "Basic " + base64.b64encode(f"{name}:{self.passwords[name]}".encode()).decode()

    def command(self, *args):
        return [str(self.binary), "--work-path", str(self.root), "--config", str(self.config), *args]

    def __enter__(self):
        with self.binary.open("rb") as binary:
            if hashlib.file_digest(binary, "sha256").hexdigest() != FORGEJO_SHA256:
                raise ValueError("Forgejo binary differs from pinned Linux amd64 release")
        run_user = pwd.getpwuid(os.getuid()).pw_name
        self.config.write_text(f"""APP_NAME = P0.1 disposable forge
RUN_MODE = prod
RUN_USER = {run_user}
[database]
DB_TYPE = sqlite3
PATH = {self.root / 'forgejo.db'}
[repository]
ROOT = {self.root / 'repositories'}
DEFAULT_BRANCH = main
[server]
HTTP_ADDR = 127.0.0.1
HTTP_PORT = {self.port}
DOMAIN = 127.0.0.1
ROOT_URL = {self.origin}/
DISABLE_SSH = true
OFFLINE_MODE = true
[security]
INSTALL_LOCK = true
[service]
DISABLE_REGISTRATION = true
[actions]
ENABLED = false
[log]
MODE = console
LEVEL = Error
""", encoding="utf-8")
        # Keep application work and configuration independent of the caller.
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith(("GITEA", "FORGEJO", "GIT_"))}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(self.root / "gitconfig"), LC_ALL="C")
        self.log = self.root / "forgejo.log"
        with self.log.open("wb") as log:
            self.process = subprocess.Popen(
                self.command("web"), cwd=self.root, env=env, stdout=log, stderr=log,
            )
        try:
            deadline = time.monotonic() + 30
            version = None
            while self.process.poll() is None and time.monotonic() < deadline:
                try:
                    status, body = api(self.origin, "/api/v1/version")
                    if status == 200:
                        version = body.get("version")
                        break
                except OSError:
                    pass
                time.sleep(0.1)
            if version != FORGEJO_VERSION:
                raise RuntimeError(f"Forgejo version probe got {version!r}, expected {FORGEJO_VERSION}")
            self.journal.record("forgejo_ready", version=version, sha256=FORGEJO_SHA256)
            for name, password in self.passwords.items():
                result = subprocess.run(
                    self.command(
                        "admin", "user", "create", "--username", name, "--password", password,
                        "--email", f"{name}@example.invalid", "--must-change-password=false",
                    ),
                    env=env, cwd=self.root, capture_output=True, text=True, timeout=TIMEOUT,
                )
                if result.returncode:
                    raise RuntimeError(result.stderr.replace(password, "[redacted]"))
            return self
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *_):
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        log = self.log.read_text(encoding="utf-8", errors="replace")
        for name, password in self.passwords.items():
            log = log.replace(password, "[redacted]").replace(self.auth(name), "[redacted]")
        self.journal.record("forgejo_exit", exit=self.process.returncode, error_log=log)

    def repo_path(self, repo):
        return f"/api/v1/repos/{OWNER}/{repo}"

    def git_url(self, repo):
        return f"{self.origin}/{OWNER}/{repo}.git"

    def call(self, path, method="GET", payload=None, user=OWNER):
        return api(self.origin, path, method, payload, self.auth(user) if user else None)

    def create_repo(self, name):
        repo = require(self.call(
            "/api/v1/user/repos", "POST",
            {"name": name, "private": False, "auto_init": False, "default_branch": "main"},
        ), 201)
        require(self.call(f"{self.repo_path(name)}/collaborators/{ACTOR}",
                          "PUT", {"permission": "write"}), 204)
        return repo["id"]

    def push(self, repo, source, sha, ref, *options, user=OWNER):
        return git("push", "--porcelain", *options, self.git_url(repo), f"{sha}:{ref}",
                   cwd=source, auth=self.auth(user), check=False)


def now():
    return datetime.now(timezone.utc).isoformat()
