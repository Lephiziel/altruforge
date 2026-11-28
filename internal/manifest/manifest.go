// Package manifest loads and validates a project manifest from a pinned tree.
package manifest

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const (
	MaxManifestBytes = 1 << 20
	MaxYAMLDepth     = 64
)

type Manifest struct {
	SchemaVersion string      `yaml:"schema_version" json:"schema_version"`
	Enabled       bool        `yaml:"enabled" json:"enabled"`
	Project       Project     `yaml:"project" json:"project"`
	Tasks         Tasks       `yaml:"tasks" json:"tasks"`
	Instructions  []string    `yaml:"instructions" json:"instructions"`
	Policy        PathPolicy  `yaml:"policy" json:"policy"`
	Agent         Agent       `yaml:"agent" json:"agent"`
	Execution     Execution   `yaml:"execution" json:"execution"`
	Checks        []Check     `yaml:"checks" json:"checks"`
	Limits        Limits      `yaml:"limits" json:"limits"`
	Publication   Publication `yaml:"publication" json:"publication"`
}
type Project struct {
	Repository    string `yaml:"repository" json:"repository"`
	DefaultBranch string `yaml:"default_branch" json:"default_branch"`
}
type Tasks struct {
	Source              string   `yaml:"source" json:"source"`
	RequiredLabels      []string `yaml:"required_labels" json:"required_labels"`
	ExcludedLabels      []string `yaml:"excluded_labels" json:"excluded_labels"`
	Selection           string   `yaml:"selection" json:"selection"`
	MaxActiveLeases     int      `yaml:"max_active_leases" json:"max_active_leases"`
	MaxOpenPullRequests int      `yaml:"max_open_pull_requests" json:"max_open_pull_requests"`
}
type PathPolicy struct {
	AllowedPaths []string `yaml:"allowed_paths" json:"allowed_paths"`
	DeniedPaths  []string `yaml:"denied_paths" json:"denied_paths"`
}
type Agent struct {
	Backend           string `yaml:"backend" json:"backend"`
	IndependentReview bool   `yaml:"independent_review" json:"independent_review"`
}
type Network struct {
	Mode       string   `yaml:"mode" json:"mode"`
	AllowHosts []string `yaml:"allow_hosts" json:"allow_hosts"`
}
type Execution struct {
	Backend  string  `yaml:"backend" json:"backend"`
	Image    string  `yaml:"image" json:"image"`
	Platform string  `yaml:"platform" json:"platform"`
	Network  Network `yaml:"network" json:"network"`
	CPUs     float64 `yaml:"cpus" json:"cpus"`
	MemoryMB int     `yaml:"memory_mb" json:"memory_mb"`
}
type Check struct {
	ID             string   `yaml:"id" json:"id"`
	Argv           []string `yaml:"argv" json:"argv"`
	TimeoutSeconds int      `yaml:"timeout_seconds" json:"timeout_seconds"`
	Required       bool     `yaml:"required" json:"required"`
}
type Limits struct {
	MaxDurationSeconds int `yaml:"max_duration_seconds" json:"max_duration_seconds"`
	MaxAttempts        int `yaml:"max_attempts" json:"max_attempts"`
}
type Publication struct {
	Draft        bool   `yaml:"draft" json:"draft"`
	AutoMerge    bool   `yaml:"auto_merge" json:"auto_merge"`
	BranchPrefix string `yaml:"branch_prefix" json:"branch_prefix"`
}

// Effective is immutable-by-convention validated policy and its pinned sources.
type Effective struct {
	Manifest     Manifest          `json:"manifest"`
	Instructions map[string]string `json:"instructions"`
	BaseCommit   string            `json:"base_commit"`
	PolicyDigest string            `json:"policy_digest"`
}
type ContributorLimits struct {
	MaxDurationSeconds int
	MaxAttempts        int
}

// Load reads the manifest and instructions exclusively from repoRoot at the given base.
// repoRoot must already identify the checked-out pinned base; callers retain BaseCommit.
func Load(r io.Reader, repoRoot, baseCommit string, contributor ContributorLimits) (*Effective, error) {
	b, err := io.ReadAll(io.LimitReader(r, MaxManifestBytes+1))
	if err != nil {
		return nil, err
	}
	if len(b) > MaxManifestBytes {
		return nil, errors.New("manifest exceeds 1 MiB limit")
	}
	var root yaml.Node
	d := yaml.NewDecoder(bytes.NewReader(b))
	if err = d.Decode(&root); err != nil {
		return nil, fmt.Errorf("decode manifest YAML: %w", err)
	}
	if len(root.Content) == 0 {
		return nil, errors.New("empty manifest")
	}
	if err = d.Decode(&yaml.Node{}); err != io.EOF {
		if err != nil {
			return nil, fmt.Errorf("decode trailing YAML: %w", err)
		}
		return nil, errors.New("multiple YAML documents are not supported")
	}
	if err = inspectNode(&root, 0); err != nil {
		return nil, err
	}
	if err = validateRequired(root.Content[0], ""); err != nil {
		return nil, err
	}
	var m Manifest
	yd := yaml.NewDecoder(bytes.NewReader(b))
	yd.KnownFields(true)
	if err = yd.Decode(&m); err != nil {
		return nil, fmt.Errorf("decode manifest fields: %w", err)
	}
	if err = validate(&m); err != nil {
		return nil, err
	}
	e := &Effective{Manifest: m, Instructions: map[string]string{}, BaseCommit: baseCommit}
	if !commitPattern.MatchString(baseCommit) {
		return nil, errors.New("base commit must be a full 40- or 64-character hexadecimal object ID")
	}
	for _, p := range m.Instructions {
		content, err := readPinned(repoRoot, p)
		if err != nil {
			return nil, fmt.Errorf("instruction %q: %w", p, err)
		}
		e.Instructions[p] = content
	}
	e.Manifest.Limits.MaxDurationSeconds = minPositive(m.Limits.MaxDurationSeconds, contributor.MaxDurationSeconds)
	e.Manifest.Limits.MaxAttempts = minPositive(m.Limits.MaxAttempts, contributor.MaxAttempts)
	e.Normalize()
	canonical, err := json.Marshal(effectiveDigestInput{e.Manifest, e.Instructions, e.BaseCommit})
	if err != nil {
		return nil, err
	}
	sum := sha256.Sum256(canonical)
	e.PolicyDigest = hex.EncodeToString(sum[:])
	return e, nil
}

type effectiveDigestInput struct {
	Manifest     Manifest          `json:"manifest"`
	Instructions map[string]string `json:"instructions"`
	BaseCommit   string            `json:"base_commit"`
}

func minPositive(a, b int) int {
	if b > 0 && b < a {
		return b
	}
	return a
}

func inspectNode(n *yaml.Node, depth int) error {
	if depth > MaxYAMLDepth {
		return errors.New("manifest exceeds YAML nesting depth limit")
	}
	if n.Anchor != "" || n.Kind == yaml.AliasNode {
		return errors.New("YAML anchors and aliases are not supported")
	}
	if n.Style&yaml.TaggedStyle != 0 {
		return fmt.Errorf("explicit YAML tags are not supported at line %d", n.Line)
	}
	if n.Tag != "" && n.Tag != "!!map" && n.Tag != "!!seq" && n.Tag != "!!str" && n.Tag != "!!bool" && n.Tag != "!!int" && n.Tag != "!!float" && n.Tag != "!!null" {
		return fmt.Errorf("unsupported YAML tag %q", n.Tag)
	}
	if n.Kind == yaml.MappingNode {
		seen := map[string]bool{}
		for i := 0; i < len(n.Content); i += 2 {
			k, v := n.Content[i], n.Content[i+1]
			if k.Value == "<<" {
				return errors.New("YAML merge keys are not supported")
			}
			if seen[k.Value] {
				return fmt.Errorf("duplicate YAML key %q at line %d", k.Value, k.Line)
			}
			seen[k.Value] = true
			if err := inspectNode(v, depth+1); err != nil {
				return err
			}
		}
	} else {
		for _, c := range n.Content {
			if err := inspectNode(c, depth+1); err != nil {
				return err
			}
		}
	}
	return nil
}

func validateRequired(n *yaml.Node, path string) error {
	required := map[string][]string{
		"":                  {"schema_version", "enabled", "project", "tasks", "instructions", "policy", "agent", "execution", "checks", "limits", "publication"},
		"project":           {"repository", "default_branch"},
		"tasks":             {"source", "required_labels", "excluded_labels", "selection", "max_active_leases", "max_open_pull_requests"},
		"policy":            {"allowed_paths", "denied_paths"},
		"agent":             {"backend", "independent_review"},
		"execution":         {"backend", "image", "platform", "network", "cpus", "memory_mb"},
		"execution.network": {"mode", "allow_hosts"},
		"limits":            {"max_duration_seconds", "max_attempts"},
		"publication":       {"draft", "auto_merge", "branch_prefix"},
	}
	if n.Kind != yaml.MappingNode {
		return fmt.Errorf("%s must be a mapping", path)
	}
	if path == "check" {
		for _, key := range []string{"id", "argv", "timeout_seconds", "required"} {
			if !mapKeys(n)[key] {
				return fmt.Errorf("missing required field checks[].%s", key)
			}
		}
	}
	keys := map[string]*yaml.Node{}
	for i := 0; i < len(n.Content); i += 2 {
		keys[n.Content[i].Value] = n.Content[i+1]
	}
	for _, key := range required[path] {
		if _, ok := keys[key]; !ok {
			return fmt.Errorf("missing required field %s", joinPath(path, key))
		}
	}
	for key, value := range keys {
		next := joinPath(path, key)
		if next == "checks" {
			if value.Kind != yaml.SequenceNode {
				return errors.New("checks must be a list")
			}
			for _, item := range value.Content {
				if err := validateRequired(item, "check"); err != nil {
					return err
				}
			}
			continue
		}
		if next == "check" {
			for _, k := range []string{"id", "argv", "timeout_seconds", "required"} {
				if _, ok := mapKeys(value)[k]; !ok {
					return fmt.Errorf("missing required field checks[].%s", k)
				}
			}
			continue
		}
		if _, ok := required[next]; ok {
			if err := validateRequired(value, next); err != nil {
				return err
			}
		}
	}
	return nil
}
func mapKeys(n *yaml.Node) map[string]bool {
	out := map[string]bool{}
	if n.Kind == yaml.MappingNode {
		for i := 0; i < len(n.Content); i += 2 {
			out[n.Content[i].Value] = true
		}
	}
	return out
}
func joinPath(a, b string) string {
	if a == "" {
		return b
	}
	return a + "." + b
}

var repoPattern = regexp.MustCompile(`^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`)
var checkIDPattern = regexp.MustCompile(`^[a-z][a-z0-9-]*$`)
var commitPattern = regexp.MustCompile(`^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$`)

func validate(m *Manifest) error {
	if m.SchemaVersion != "0.1" {
		return fmt.Errorf("unsupported schema_version %q", m.SchemaVersion)
	}
	if !repoPattern.MatchString(m.Project.Repository) || m.Project.DefaultBranch == "" {
		return errors.New("invalid project repository or default_branch")
	}
	if m.Tasks.Source != "github_issues" || len(m.Tasks.RequiredLabels) == 0 || !oneOf(m.Tasks.Selection, "agent_ranked", "oldest_first") || !between(m.Tasks.MaxActiveLeases, 1, 100) || !between(m.Tasks.MaxOpenPullRequests, 1, 100) {
		return errors.New("invalid task source, labels, selection, or limits")
	}
	if err := uniqueNonempty(m.Tasks.RequiredLabels, "required_labels"); err != nil {
		return err
	}
	if err := uniqueNonempty(m.Tasks.ExcludedLabels, "excluded_labels"); err != nil {
		return err
	}
	if len(m.Instructions) == 0 {
		return errors.New("at least one instruction path is required")
	}
	if err := uniqueNonempty(m.Instructions, "instructions"); err != nil {
		return err
	}
	for _, p := range m.Instructions {
		if err := validateRepoPath(p, false); err != nil {
			return fmt.Errorf("invalid instruction path %q: %w", p, err)
		}
	}
	if len(m.Policy.AllowedPaths) == 0 || len(m.Policy.DeniedPaths) == 0 {
		return errors.New("allowed_paths and denied_paths must not be empty")
	}
	if err := uniqueNonempty(m.Policy.AllowedPaths, "allowed_paths"); err != nil {
		return err
	}
	if err := uniqueNonempty(m.Policy.DeniedPaths, "denied_paths"); err != nil {
		return err
	}
	for _, p := range append(append([]string{}, m.Policy.AllowedPaths...), m.Policy.DeniedPaths...) {
		if err := validateRepoPath(p, true); err != nil {
			return fmt.Errorf("invalid policy path %q: %w", p, err)
		}
		for _, segment := range strings.Split(p, "/") {
			if _, err := filepath.Match(segment, segment); err != nil {
				return fmt.Errorf("invalid policy glob %q: %w", p, err)
			}
		}
	}
	for _, g := range m.Policy.AllowedPaths {
		for _, protectedPath := range []string{".altruforge/project.yaml", ".github/workflows/ci.yml", ".git/config", ".env", "secrets/token", "credentials.json"} {
			if match(g, protectedPath) {
				return fmt.Errorf("allowed_paths grants protected path %q", g)
			}
		}
	}
	if m.Agent.Backend != "codex" || !m.Agent.IndependentReview {
		return errors.New("unsupported agent configuration")
	}
	if m.Execution.Backend != "docker" || m.Execution.Image == "" || !oneOf(m.Execution.Platform, "linux/amd64", "linux/arm64") || m.Execution.CPUs <= 0 || m.Execution.MemoryMB < 256 {
		return errors.New("invalid execution configuration")
	}
	if m.Execution.Network.Mode == "deny" && len(m.Execution.Network.AllowHosts) != 0 {
		return errors.New("network deny mode cannot have allow_hosts")
	}
	if !oneOf(m.Execution.Network.Mode, "deny", "allowlist") {
		return errors.New("unsupported network mode")
	}
	if m.Execution.Network.Mode == "allowlist" && len(m.Execution.Network.AllowHosts) == 0 {
		return errors.New("allowlist network mode requires at least one host")
	}
	if err := uniqueNonempty(m.Execution.Network.AllowHosts, "allow_hosts"); err != nil {
		return err
	}
	for _, h := range m.Execution.Network.AllowHosts {
		if err := validateHost(h); err != nil {
			return fmt.Errorf("invalid network host %q: %w", h, err)
		}
	}
	if len(m.Checks) == 0 {
		return errors.New("at least one check is required")
	}
	ids := map[string]bool{}
	for _, c := range m.Checks {
		if !checkIDPattern.MatchString(c.ID) || ids[c.ID] {
			return fmt.Errorf("invalid or duplicate check id %q", c.ID)
		}
		ids[c.ID] = true
		if len(c.Argv) == 0 || c.TimeoutSeconds < 1 || c.TimeoutSeconds > 3600 {
			return fmt.Errorf("invalid check %q", c.ID)
		}
		for _, a := range c.Argv {
			if a == "" {
				return fmt.Errorf("check %q has empty argv item", c.ID)
			}
		}
	}
	if !between(m.Limits.MaxDurationSeconds, 1, 86400) || !between(m.Limits.MaxAttempts, 1, 10) {
		return errors.New("invalid project limits")
	}
	if !m.Publication.Draft || m.Publication.AutoMerge || strings.TrimSpace(m.Publication.BranchPrefix) == "" || strings.ContainsAny(m.Publication.BranchPrefix, " ~^:?*[\\") {
		return errors.New("invalid publication configuration")
	}
	return nil
}
func validateHost(h string) error {
	if h == "" || strings.ContainsAny(h, " /\\\t\n") {
		return errors.New("expected hostname without scheme or path")
	}
	if strings.Contains(h, "*") {
		return errors.New("wildcards are not allowed")
	}
	host := h
	if strings.HasPrefix(h, "[") {
		var err error
		host, _, err = net.SplitHostPort(h)
		if err != nil || net.ParseIP(host) == nil {
			return errors.New("invalid bracketed IP host:port")
		}
	} else if strings.Count(h, ":") == 1 {
		var err error
		var port string
		host, port, err = net.SplitHostPort(h)
		if err != nil {
			return errors.New("invalid host:port")
		}
		n, err := strconv.Atoi(port)
		if err != nil || n < 1 || n > 65535 {
			return errors.New("invalid host port")
		}
	} else if strings.Contains(h, ":") && net.ParseIP(h) == nil {
		return errors.New("invalid host")
	}
	if ip := net.ParseIP(host); ip == nil {
		if len(host) > 253 || host == "" {
			return errors.New("invalid hostname")
		}
		for _, label := range strings.Split(host, ".") {
			if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
				return errors.New("invalid hostname")
			}
			for _, r := range label {
				if !(r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '-') {
					return errors.New("invalid hostname")
				}
			}
		}
	}
	return nil
}
func uniqueNonempty(s []string, name string) error {
	seen := map[string]bool{}
	for _, v := range s {
		if strings.TrimSpace(v) == "" || seen[v] {
			return fmt.Errorf("empty or duplicate %s entry %q", name, v)
		}
		seen[v] = true
	}
	return nil
}
func oneOf(s string, choices ...string) bool {
	for _, v := range choices {
		if s == v {
			return true
		}
	}
	return false
}
func between(v, lo, hi int) bool { return v >= lo && v <= hi }

// Allowed reports whether a changed repository-relative path satisfies the policy.
func (p PathPolicy) Allowed(path string) bool {
	if validateRepoPath(path, false) != nil || protected(path) {
		return false
	}
	ok := false
	for _, g := range p.AllowedPaths {
		if match(g, path) {
			ok = true
			break
		}
	}
	if !ok {
		return false
	}
	for _, g := range p.DeniedPaths {
		if match(g, path) {
			return false
		}
	}
	return true
}

// CanStartContribution is the mandatory gate before creating any run state.
func (e *Effective) CanStartContribution() bool { return e != nil && e.Manifest.Enabled }
func protected(p string) bool {
	p = strings.ToLower(strings.TrimPrefix(filepath.ToSlash(p), "./"))
	for _, g := range []string{".git/**", ".altruforge/**", ".github/workflows/**", "**/.env", "**/.env.*", "**/*credentials*", "**/*secret*", "**/*token*", "**/*private-key*"} {
		if match(g, p) {
			return true
		}
	}
	return p == ".git" || p == ".altruforge" || p == ".github/workflows"
}
func validateRepoPath(p string, pattern bool) error {
	if p == "" || strings.Contains(p, "\\") || strings.HasPrefix(p, "/") || filepath.IsAbs(p) {
		return errors.New("must be a relative slash-separated path")
	}
	if strings.Contains(p, "//") {
		return errors.New("empty path segment")
	}
	for _, s := range strings.Split(p, "/") {
		if s == "." || s == ".." || s == "" {
			return errors.New("dot and parent segments are not allowed")
		}
		if strings.ContainsAny(s, "\x00") {
			return errors.New("NUL is not allowed")
		}
		if !pattern && strings.ContainsAny(s, "*?[") {
			return errors.New("glob characters are not allowed")
		}
	}
	return nil
}
func match(pattern, path string) bool {
	ps := strings.Split(pattern, "/")
	xs := strings.Split(path, "/")
	var f func(int, int) bool
	f = func(i, j int) bool {
		if i == len(ps) {
			return j == len(xs)
		}
		if ps[i] == "**" {
			for k := j; k <= len(xs); k++ {
				if f(i+1, k) {
					return true
				}
			}
			return false
		}
		if j == len(xs) {
			return false
		}
		ok, e := filepath.Match(ps[i], xs[j])
		return e == nil && ok && f(i+1, j+1)
	}
	return f(0, 0)
}

func readPinned(root, rel string) (string, error) {
	abs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	abs, err = filepath.EvalSymlinks(abs)
	if err != nil {
		return "", err
	}
	candidate := filepath.Join(abs, filepath.FromSlash(rel))
	resolved, err := filepath.EvalSymlinks(candidate)
	if err != nil {
		return "", err
	}
	resolved, err = filepath.Abs(resolved)
	if err != nil {
		return "", err
	}
	r, err := filepath.Rel(abs, resolved)
	if err != nil || r == ".." || strings.HasPrefix(r, ".."+string(filepath.Separator)) {
		return "", errors.New("instruction resolves outside pinned repository")
	}
	st, err := os.Stat(resolved)
	if err != nil {
		return "", err
	}
	if !st.Mode().IsRegular() {
		return "", errors.New("instruction is not a regular file")
	}
	b, err := os.ReadFile(resolved)
	return string(b), err
}

// Normalize sorts set-valued policy fields for stable display and hashing.
func (e *Effective) Normalize() {
	sort.Strings(e.Manifest.Policy.AllowedPaths)
	sort.Strings(e.Manifest.Policy.DeniedPaths)
	sort.Strings(e.Manifest.Tasks.RequiredLabels)
	sort.Strings(e.Manifest.Tasks.ExcludedLabels)
	sort.Strings(e.Manifest.Execution.Network.AllowHosts)
}
