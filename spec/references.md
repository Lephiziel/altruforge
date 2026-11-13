# Technical references

Reviewed during planning on 2026-11-13. These sources describe external capabilities; they are not evidence that Altruforge has implemented them.

| Source | Relevance |
| --- | --- |
| [Codex app-server](https://learn.chatgpt.com/docs/app-server) | Account/session integration and streamed protocol |
| [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) | Official higher-level SDK alternatives |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | SDK languages and supported subprocess route |
| [Programmatic Claude Code](https://code.claude.com/docs/en/headless) | Structured CLI output and lifecycle options |
| [Docker Engine SDK](https://docs.docker.com/reference/api/engine/sdk/) | Executor API and Go SDK |
| [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/install) | Host requirements for a possible additional backend |
| [Go os/exec](https://pkg.go.dev/os/exec) | Process lifecycle primitives |
| [Go plugin](https://pkg.go.dev/plugin) | Dynamic plugin portability constraints |
| [modernc SQLite](https://pkg.go.dev/modernc.org/sqlite) | CGO-free storage and platform targets |
| [Cobra](https://github.com/spf13/cobra) | CLI command infrastructure |
| [go-github](https://github.com/google/go-github) | Go GitHub API client |
| [YAML org parser](https://github.com/yaml/go-yaml) | Maintained Go YAML parser |
| [JSON Schema validator](https://github.com/santhosh-tekuri/jsonschema) | Go contract validation candidate |
| [Apache-2.0](https://apache.org/licenses/LICENSE-2.0.html) | License terms |

Pin actual versions and recheck relevant provider behavior when implementing an adapter. Subscription/account support is determined by the provider's current supported integration.
