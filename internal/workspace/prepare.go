// Package workspace prepares pinned public GitHub contribution workspaces.
package workspace

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	gh "github.com/Lephiziel/altruforge/internal/forge/github"
	"gopkg.in/yaml.v3"
)

// GitRunner is injectable so workspace operations can be tested without a network.
type GitRunner interface {
	Run(context.Context, string, ...string) ([]byte, error)
}

type Preparer struct {
	Git    GitRunner
	GitHub gh.Client
}

type OptIn struct {
	Enabled bool `yaml:"enabled"`
	Project struct {
		Repository string `yaml:"repository"`
	} `yaml:"project"`
}

type Result struct {
	Path, BaseCommit, Branch, Fork string
	ExistingFork                   bool
}

// Prepare reads only a public repository, validates its base-revision opt-in,
// pins that base, and configures a contributor-owned fork as the push remote.
func (p Preparer) Prepare(ctx context.Context, slug, path, branch string) (Result, error) {
	if !validBranch(branch) {
		return Result{}, errors.New("branch name is invalid")
	}
	if p.Git == nil {
		p.Git = gh.ExecRunner{}
	}
	account, err := p.GitHub.Account(ctx)
	if err != nil {
		return Result{}, err
	}
	repo, err := p.GitHub.PublicRepository(ctx, slug)
	if err != nil {
		return Result{}, err
	}
	if !strings.EqualFold(repo.FullName, slug) {
		return Result{}, errors.New("GitHub repository identity mismatch")
	}
	cloneURL, err := url.Parse(repo.CloneURL)
	if err != nil || cloneURL.Scheme != "https" || !strings.EqualFold(cloneURL.Host, "github.com") {
		return Result{}, errors.New("GitHub returned an unsupported clone URL")
	}
	if path == "" {
		return Result{}, errors.New("workspace path is required")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return Result{}, fmt.Errorf("resolve workspace path: %w", err)
	}
	if _, err := os.Lstat(abs); err == nil {
		return Result{}, errors.New("workspace path already exists")
	} else if !errors.Is(err, os.ErrNotExist) {
		return Result{}, fmt.Errorf("inspect workspace path: %w", err)
	}
	// Create parent directories, but reserve the actual destination exclusively.
	if err := os.MkdirAll(filepath.Dir(abs), 0o700); err != nil {
		return Result{}, fmt.Errorf("create workspace parent: %w", err)
	}
	if err := os.Mkdir(abs, 0o700); err != nil {
		return Result{}, fmt.Errorf("reserve workspace: %w", err)
	}
	cleanup := true
	defer func() {
		if cleanup {
			_ = os.RemoveAll(abs)
		}
	}()
	if _, err := p.Git.Run(ctx, "git", "clone", "--branch", repo.DefaultBranch, "--single-branch", "--", repo.CloneURL, abs); err != nil {
		return Result{}, fmt.Errorf("clone public repository: %w", err)
	}
	var opt OptIn
	data, err := os.ReadFile(filepath.Join(abs, ".altruforge", "project.yaml"))
	if err != nil {
		return Result{}, errors.New("public target has no project opt-in manifest")
	}
	var document yaml.Node
	if err := yaml.Unmarshal(data, &document); err != nil || hasDuplicateKeys(&document) {
		return Result{}, errors.New("public target opt-in manifest is invalid")
	}
	if err := document.Decode(&opt); err != nil {
		return Result{}, errors.New("public target opt-in manifest is invalid")
	}
	if !opt.Enabled || !strings.EqualFold(opt.Project.Repository, repo.FullName) {
		return Result{}, errors.New("project has not opted in for this repository")
	}
	base, err := p.Git.Run(ctx, "git", "-C", abs, "rev-parse", "refs/remotes/origin/"+repo.DefaultBranch+"^{commit}")
	if err != nil {
		return Result{}, errors.New("cannot resolve trusted default-branch commit")
	}
	commit := strings.TrimSpace(string(base))
	if len(commit) != 40 {
		return Result{}, errors.New("Git returned an invalid base commit")
	}
	_, forkErr := p.GitHub.Fork(ctx, repo, account)
	existingFork := isExistingFork(forkErr)
	if forkErr != nil && !existingFork {
		return Result{}, forkErr
	}
	forkSlug := account + "/" + repo.FullName[strings.IndexByte(repo.FullName, '/')+1:]
	fork, err := p.GitHub.PublicRepository(ctx, forkSlug)
	if err != nil {
		return Result{}, err
	}
	if !fork.Fork || !strings.EqualFold(fork.Owner.Login, account) {
		return Result{}, errors.New("GitHub fork is not owned by the active contributor")
	}
	if _, err := p.Git.Run(ctx, "git", "-C", abs, "remote", "add", "contributor", fork.CloneURL); err != nil {
		return Result{}, errors.New("cannot configure contributor fork remote")
	}
	if _, err := p.Git.Run(ctx, "git", "-C", abs, "checkout", "--detach", commit); err != nil {
		return Result{}, errors.New("cannot pin workspace to trusted base")
	}
	if _, err := p.Git.Run(ctx, "git", "-C", abs, "switch", "-c", branch, commit); err != nil {
		return Result{}, errors.New("cannot create contribution branch")
	}
	cleanup = false
	return Result{Path: abs, BaseCommit: commit, Branch: branch, Fork: fork.FullName, ExistingFork: existingFork}, nil
}

func validBranch(s string) bool {
	return s != "" && !strings.HasPrefix(s, "-") && !strings.ContainsAny(s, "\x00\r\n")
}
func isExistingFork(err error) bool {
	var e *gh.Error
	return errors.As(err, &e) && e.Class == gh.ExistingFork
}

func hasDuplicateKeys(node *yaml.Node) bool {
	if node == nil {
		return false
	}
	if node.Kind == yaml.MappingNode {
		seen := map[string]bool{}
		for i := 0; i+1 < len(node.Content); i += 2 {
			key := node.Content[i]
			if key.Kind != yaml.ScalarNode || seen[key.Value] {
				return true
			}
			seen[key.Value] = true
		}
	}
	for _, child := range node.Content {
		if hasDuplicateKeys(child) {
			return true
		}
	}
	return node.Kind == yaml.AliasNode
}
