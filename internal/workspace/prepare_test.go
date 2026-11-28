package workspace

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	gh "github.com/Lephiziel/altruforge/internal/forge/github"
)

type forgeFixture struct{ account, upstream, fork string }

func (f forgeFixture) Run(_ context.Context, name string, args ...string) ([]byte, error) {
	if name != "gh" {
		return nil, fmt.Errorf("unexpected command %s", name)
	}
	switch {
	case strings.Join(args, " ") == "auth status --hostname github.com":
		return []byte("ok"), nil
	case strings.Join(args, " ") == "api user --jq .login":
		return []byte(f.account), nil
	case strings.HasPrefix(strings.Join(args, " "), "api repos/org/source/forks --paginate --jq "):
		return nil, nil
	case strings.Join(args, " ") == "repo fork org/source --clone=false":
		return []byte("forked"), nil
	case strings.Join(args, " ") == "api repos/org/source":
		return []byte(f.upstream), nil
	case strings.Join(args, " ") == "api repos/contributor/source":
		return []byte(f.fork), nil
	default:
		return nil, fmt.Errorf("unexpected gh call: %s", strings.Join(args, " "))
	}
}

type localGit struct{ source string }

func (g localGit) Run(ctx context.Context, name string, args ...string) ([]byte, error) {
	if name == "git" && len(args) == 7 && args[0] == "clone" && args[4] == "--" {
		args[5] = g.source
	}
	return gh.ExecRunner{}.Run(ctx, name, args...)
}

func TestPrepareClonesPinsOptedInBaseAndHandlesUnicodePath(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "source repo")
	if err := os.MkdirAll(filepath.Join(source, ".altruforge"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, ".altruforge", "project.yaml"), []byte("enabled: true\nproject:\n  repository: org/source\n"), 0600); err != nil {
		t.Fatal(err)
	}
	git(t, source, "init", "-b", "main")
	git(t, source, "add", ".")
	git(t, source, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "base")
	commit := strings.TrimSpace(git(t, source, "rev-parse", "HEAD"))
	upstream, _ := json.Marshal(map[string]any{"full_name": "org/source", "visibility": "public", "clone_url": "https://github.com/org/source.git", "default_branch": "main"})
	fork, _ := json.Marshal(map[string]any{"full_name": "contributor/source", "visibility": "public", "clone_url": "https://github.com/contributor/source.git", "default_branch": "main", "fork": true, "owner": map[string]string{"login": "contributor"}})
	path := filepath.Join(root, "work space", "café")
	result, err := (Preparer{Git: localGit{source}, GitHub: gh.Client{Runner: forgeFixture{"contributor", string(upstream), string(fork)}}}).Prepare(context.Background(), "org/source", path, "altruforge/task-1")
	if err != nil {
		t.Fatal(err)
	}
	if result.BaseCommit != commit || result.Path != path || result.Fork != "contributor/source" {
		t.Fatalf("unexpected result: %#v", result)
	}
	if got := git(t, path, "rev-parse", "HEAD"); strings.TrimSpace(got) != commit {
		t.Fatalf("HEAD = %q, want %q", got, commit)
	}
	if got := git(t, path, "branch", "--show-current"); strings.TrimSpace(got) != "altruforge/task-1" {
		t.Fatalf("branch = %q", got)
	}
	if got := git(t, path, "remote", "get-url", "contributor"); strings.TrimSpace(got) != "https://github.com/contributor/source.git" {
		t.Fatalf("fork remote = %q", got)
	}
}

func TestPrepareRequiresOptInAndDoesNotOverwriteExistingDirectory(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "src")
	if err := os.MkdirAll(filepath.Join(source, ".altruforge"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, ".altruforge", "project.yaml"), []byte("enabled: false\nproject:\n  repository: org/source\n"), 0600); err != nil {
		t.Fatal(err)
	}
	git(t, source, "init", "-b", "main")
	git(t, source, "add", ".")
	git(t, source, "-c", "user.name=T", "-c", "user.email=t@invalid", "commit", "-m", "base")
	upstream, _ := json.Marshal(map[string]any{"full_name": "org/source", "visibility": "public", "clone_url": "https://github.com/org/source.git", "default_branch": "main"})
	fork, _ := json.Marshal(map[string]any{"full_name": "contributor/source", "visibility": "public", "clone_url": "https://github.com/contributor/source.git", "default_branch": "main", "fork": true, "owner": map[string]string{"login": "contributor"}})
	p := Preparer{Git: localGit{source}, GitHub: gh.Client{Runner: forgeFixture{"contributor", string(upstream), string(fork)}}}
	path := filepath.Join(root, "workspace")
	if _, err := p.Prepare(context.Background(), "org/source", path, "topic"); err == nil {
		t.Fatal("disabled project accepted")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("workspace retained after rejected opt-in: %v", err)
	}
	if err := os.Mkdir(path, 0700); err != nil {
		t.Fatal(err)
	}
	if _, err := p.Prepare(context.Background(), "org/source", path, "topic"); err == nil {
		t.Fatal("existing directory accepted")
	}
}

func git(t *testing.T, dir string, args ...string) string {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v: %s", args, err, out)
	}
	return string(out)
}
