// Package github implements the supported GitHub CLI integration.
package github

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// Runner is the narrow process boundary used by the adapter and its tests.
type Runner interface {
	Run(context.Context, string, ...string) ([]byte, error)
}

// ExecRunner invokes programs using argument arrays (never a shell).
type ExecRunner struct{}

func (ExecRunner) Run(ctx context.Context, name string, args ...string) ([]byte, error) {
	cmd := exec.CommandContext(ctx, name, args...)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	out, err := cmd.Output()
	if err != nil {
		var exit *exec.ExitError
		if errors.As(err, &exit) {
			return nil, &Error{Class: classifyText(stderr.String()), Err: fmt.Errorf("%s failed (exit %d)", name, exit.ExitCode())}
		}
		return nil, fmt.Errorf("cannot run %s: %w", name, err)
	}
	return out, nil
}

// Failure classifies stable, actionable GitHub integration failures.
type Failure string

const (
	AuthenticationRevoked Failure = "authentication_revoked"
	MissingAccess         Failure = "missing_access"
	NetworkFailure        Failure = "network_failure"
	ExistingFork          Failure = "existing_fork"
	DependencyUnavailable Failure = "dependency_unavailable"
)

// Error is a redacted adapter failure; it never includes command output.
type Error struct {
	Class Failure
	Err   error
}

func (e *Error) Error() string { return string(e.Class) }
func (e *Error) Unwrap() error { return e.Err }

// Client relies on the user's existing gh authentication. It never owns or
// deletes that global session.
type Client struct{ Runner Runner }

func (c Client) runner() Runner {
	if c.Runner != nil {
		return c.Runner
	}
	return ExecRunner{}
}

// Account verifies gh authentication and returns the active login only.
func (c Client) Account(ctx context.Context) (string, error) {
	r := c.runner()
	if _, err := r.Run(ctx, "gh", "auth", "status", "--hostname", "github.com"); err != nil {
		return "", classify(err, true)
	}
	out, err := r.Run(ctx, "gh", "api", "user", "--jq", ".login")
	if err != nil {
		return "", classify(err, false)
	}
	login := strings.TrimSpace(string(out))
	if login == "" || strings.ContainsAny(login, "\r\n") {
		return "", errors.New("GitHub returned an invalid account login")
	}
	return login, nil
}

// Repository describes only the public repository fields needed by workspace setup.
type Repository struct {
	FullName      string `json:"full_name"`
	CloneURL      string `json:"clone_url"`
	DefaultBranch string `json:"default_branch"`
	Visibility    string `json:"visibility"`
	Fork          bool   `json:"fork"`
	Owner         struct {
		Login string `json:"login"`
	} `json:"owner"`
}

func (c Client) PublicRepository(ctx context.Context, slug string) (Repository, error) {
	if !validSlug(slug) {
		return Repository{}, errors.New("repository must be owner/repo")
	}
	out, err := c.runner().Run(ctx, "gh", "api", "repos/"+slug)
	if err != nil {
		return Repository{}, classify(err, false)
	}
	var repo Repository
	if err := json.Unmarshal(out, &repo); err != nil {
		return Repository{}, errors.New("invalid GitHub repository response")
	}
	if repo.FullName == "" || repo.Visibility != "public" || repo.CloneURL == "" || repo.DefaultBranch == "" {
		return Repository{}, errors.New("target must be a public GitHub repository")
	}
	return repo, nil
}

func (c Client) Fork(ctx context.Context, repo Repository, account string) (Repository, error) {
	forkSlug := account + "/" + repo.FullName[strings.IndexByte(repo.FullName, '/')+1:]
	out, err := c.runner().Run(ctx, "gh", "api", "repos/"+repo.FullName+"/forks", "--paginate", "--jq", ".[] | select(.owner.login == "+jsonQuote(account)+")")
	if err != nil {
		return Repository{}, classify(err, false)
	}
	if strings.TrimSpace(string(out)) != "" {
		var existing Repository
		if json.Unmarshal(out, &existing) != nil || !existing.Fork {
			return Repository{}, &Error{Class: MissingAccess}
		}
		return existing, &Error{Class: ExistingFork}
	}
	if _, err = c.runner().Run(ctx, "gh", "repo", "fork", repo.FullName, "--clone=false"); err != nil {
		return Repository{}, classify(err, false)
	}
	out, err = c.runner().Run(ctx, "gh", "api", "repos/"+forkSlug)
	if err != nil {
		return Repository{}, classify(err, false)
	}
	var fork Repository
	if json.Unmarshal(out, &fork) != nil || !fork.Fork {
		return Repository{}, errors.New("GitHub did not return the created fork")
	}
	return fork, nil
}

func jsonQuote(s string) string { b, _ := json.Marshal(s); return string(b) }

func validSlug(s string) bool {
	p := strings.Split(s, "/")
	if len(p) != 2 {
		return false
	}
	for _, v := range p {
		if v == "" || strings.ContainsAny(v, " .\\\t\r\n") {
			return false
		}
	}
	return true
}

func classify(err error, auth bool) error {
	if err == nil {
		return nil
	}
	var known *Error
	if errors.As(err, &known) {
		return known
	}
	if errors.Is(err, exec.ErrNotFound) || errors.Is(err, os.ErrNotExist) {
		return &Error{Class: DependencyUnavailable, Err: err}
	}
	class := classifyText(err.Error())
	if auth && class == NetworkFailure {
		class = AuthenticationRevoked
	}
	return &Error{Class: class, Err: err}
}

func classifyText(text string) Failure {
	s := strings.ToLower(text)
	switch {
	case strings.Contains(s, "401"), strings.Contains(s, "auth"):
		return AuthenticationRevoked
	case strings.Contains(s, "403"), strings.Contains(s, "404"), strings.Contains(s, "access"), strings.Contains(s, "permission"):
		return MissingAccess
	case strings.Contains(s, "token"):
		return AuthenticationRevoked
	default:
		return NetworkFailure
	}
}
