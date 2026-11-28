package manifest

import (
	"os"
	"strings"
	"testing"
)

func fixture(t *testing.T) string {
	t.Helper()
	b, err := os.ReadFile("../../examples/project.yaml")
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}
func loadText(t *testing.T, s string) (*Effective, error) {
	t.Helper()
	return Load(strings.NewReader(s), "../..", strings.Repeat("0", 40), ContributorLimits{MaxDurationSeconds: 900, MaxAttempts: 1})
}

func TestLoadDisabledAndEffectivePolicy(t *testing.T) {
	e, err := loadText(t, fixture(t))
	if err != nil {
		t.Fatal(err)
	}
	if e.CanStartContribution() {
		t.Fatal("disabled project became runnable")
	}
	if len(e.BaseCommit) != 40 || len(e.PolicyDigest) != 64 {
		t.Fatalf("missing pinned provenance/digest: %#v", e)
	}
	if e.Manifest.Limits.MaxDurationSeconds != 900 || e.Manifest.Limits.MaxAttempts != 1 {
		t.Fatalf("limits not reduced: %+v", e.Manifest.Limits)
	}
}

func TestLoadRejectsStrictYAMLAndRuntimeViolations(t *testing.T) {
	base := fixture(t)
	cases := []struct{ name, input string }{
		{"duplicate key", "schema_version: '0.1'\nschema_version: '0.1'"},
		{"alias", strings.Replace(base, "instructions:\n- AGENTS.md\n- .altruforge/instructions.md", "instructions:\n- &i AGENTS.md\n- *i", 1)},
		{"merge", strings.Replace(base, "project:\n  repository:", "project:\n  <<: {}\n  repository:", 1)},
		{"custom tag", strings.Replace(base, "enabled: false", "enabled: !custom false", 1)},
		{"unknown field", strings.Replace(base, "enabled: false", "enabled: false\nunknown: true", 1)},
		{"missing required field", strings.Replace(base, "  auto_merge: false\n", "", 1)},
		{"unsupported version", strings.Replace(base, "schema_version: '0.1'", "schema_version: '9'", 1)},
		{"duplicate check id", strings.Replace(base, "- id: vet", "- id: tests", 1)},
		{"invalid network", strings.Replace(base, "mode: allowlist", "mode: deny", 1)},
		{"absolute instruction", strings.Replace(base, "- AGENTS.md", "- /etc/passwd", 1)},
		{"traversal instruction", strings.Replace(base, "- AGENTS.md", "- ../AGENTS.md", 1)},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if _, err := loadText(t, tc.input); err == nil {
				t.Fatal("expected rejection")
			}
		})
	}
}

func TestLoadRejectsDocumentSizeAndDepth(t *testing.T) {
	base := fixture(t)
	if _, err := loadText(t, base+"\n---\n{}"); err == nil {
		t.Fatal("accepted second document")
	}
	if _, err := Load(strings.NewReader(strings.Repeat(" ", MaxManifestBytes+1)), "../..", strings.Repeat("0", 40), ContributorLimits{}); err == nil {
		t.Fatal("accepted oversized input")
	}
	if _, err := loadText(t, "x: "+strings.Repeat("[", MaxYAMLDepth+2)+"null"+strings.Repeat("]", MaxYAMLDepth+2)); err == nil {
		t.Fatal("accepted deep YAML")
	}
}

func TestPathPolicyDenyProtectedAndTraversal(t *testing.T) {
	p := PathPolicy{AllowedPaths: []string{"**"}, DeniedPaths: []string{"internal/private/**"}}
	for _, path := range []string{"README.md", "internal/manifest/a.go"} {
		if !p.Allowed(path) {
			t.Errorf("unexpected denied path %q", path)
		}
	}
	for _, path := range []string{"internal/private/key", "../outside", "/absolute", ".altruforge/project.yaml", ".github/workflows/go.yml", "secret-token.txt"} {
		if p.Allowed(path) {
			t.Errorf("unexpected allowed path %q", path)
		}
	}
}

func TestInstructionSymlinkCannotEscape(t *testing.T) {
	root := t.TempDir()
	outside := t.TempDir() + "/outside"
	if err := os.WriteFile(outside, []byte("secret"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, root+"/escape"); err != nil {
		t.Skipf("symlink unavailable: %v", err)
	}
	if _, err := readPinned(root, "escape"); err == nil {
		t.Fatal("accepted symlink escape")
	}
}

func TestPatternsAndDigestCanonicalization(t *testing.T) {
	p := PathPolicy{AllowedPaths: []string{"internal/**"}}
	if !p.Allowed("internal/manifest/a.go") || p.Allowed("docs/a.md") {
		t.Fatal("glob matching incorrect")
	}
	s := fixture(t)
	a, err := loadText(t, s)
	if err != nil {
		t.Fatal(err)
	}
	b, err := loadText(t, strings.Replace(s, "  - cmd/**\n  - internal/**", "  - internal/**\n  - cmd/**", 1))
	if err != nil {
		t.Fatal(err)
	}
	if a.PolicyDigest != b.PolicyDigest {
		t.Fatal("set-valued path order changed normalized digest")
	}
}
