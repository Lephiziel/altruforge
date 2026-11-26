package manifest

import "testing"

func TestPathValidation(t *testing.T) {
	for _, path := range []string{
		"", "/etc/passwd", "//server/share", "C:/repo/file", "c:file",
		`C:\repo\file`, `\\server\share`, `docs\file`, "../file",
		"docs/../file", "docs/..", ".", "./file", "docs/./file",
		"docs//file", "docs/", "docs/stream:name", "a\x00b", "a\xffb",
	} {
		t.Run(path, func(t *testing.T) {
			if err := ValidatePath(path); err == nil {
				t.Fatalf("ValidatePath(%q) accepted unsafe input", path)
			}
			if err := ValidatePattern(path); err == nil {
				t.Fatalf("ValidatePattern(%q) accepted unsafe input", path)
			}
			if ok, err := MatchPath("**", path); ok || err == nil {
				t.Fatalf("MatchPath accepted invalid path: %v, %v", ok, err)
			}
			if ok, err := MatchPath(path, "safe"); ok || err == nil {
				t.Fatalf("MatchPath accepted invalid pattern: %v, %v", ok, err)
			}
		})
	}
	for _, path := range []string{"README.md", "docs/日本語 file.md", ".github/workflows/check.yml", "a/.../b"} {
		if err := ValidatePath(path); err != nil {
			t.Errorf("ValidatePath(%q): %v", path, err)
		}
	}
}

func TestMatchPath(t *testing.T) {
	tests := []struct {
		pattern string
		path    string
		want    bool
	}{
		{"README.md", "README.md", true},
		{"README.md", "readme.md", false},
		{"docs", "docs/a", false},
		{"docs/a", "x/docs/a", false},
		{"docs/*", "docs/a", true},
		{"docs/*", "docs/a/b", false},
		{"docs/*", "docs", false},
		{"a*b", "ab", true},
		{"a*b", "axyb", true},
		{"a*b", "axyb/z", false},
		{"docs/**", "docs", true},
		{"docs/**", "docs/a/b", true},
		{"docs/**", "docs-other/a", false},
		{"**/file", "file", true},
		{"**/file", "a/b/file", true},
		{"a/**/b", "a/b", true},
		{"a/**/b", "a/x/y/b", true},
		{"a/**/b", "a/x/b/c", false},
		{"**/**/b", "b", true},
		{"**/**/b", "x/y/b", true},
		{"**", "日本語/spaced name", true},
		{"docs/日本語 *.md", "docs/日本語 file.md", true},
		{"docs/日本語 *.md", "docs/日本語 .md", true},
		{"file?.md", "file1.md", false},
		{"file?.md", "file?.md", true},
		{"[ab]", "a", false},
		{"[ab]", "[ab]", true},
		{"{a,b}", "a", false},
		{"{a,b}", "{a,b}", true},
	}
	for _, tt := range tests {
		t.Run(tt.pattern+":"+tt.path, func(t *testing.T) {
			got, err := MatchPath(tt.pattern, tt.path)
			if err != nil || got != tt.want {
				t.Fatalf("MatchPath(%q, %q) = %v, %v; want %v", tt.pattern, tt.path, got, err, tt.want)
			}
		})
	}
	for _, pattern := range []string{"a**", "**b", "a/***/b", "a/x**y"} {
		if ok, err := MatchPath(pattern, "a/b"); ok || err == nil {
			t.Errorf("unsupported pattern %q: %v, %v", pattern, ok, err)
		}
	}
}

func TestPathAllowed(t *testing.T) {
	tests := []struct {
		name    string
		path    string
		allowed []string
		denied  []string
		want    bool
		invalid bool
	}{
		{"allowed", "docs/a", []string{"docs/**"}, nil, true, false},
		{"no match", "cmd/a", []string{"docs/**"}, nil, false, false},
		{"no allows", "docs/a", nil, nil, false, false},
		{"deny wins", "docs/private/a", []string{"**"}, []string{"docs/private/**"}, false, false},
		{"exact allow denied", "LICENSE", []string{"LICENSE", "**"}, []string{"LICENSE"}, false, false},
		{"workflow protected", ".github/workflows/check.yml", []string{"**"}, []string{".github/**"}, false, false},
		{"manifest protected", ".altruforge/project.yaml", []string{"**"}, []string{".altruforge/**"}, false, false},
		{"segment boundary", "docs/public/a", []string{"**"}, []string{"docs/private/**"}, true, false},
		{"unicode spaces", "docs/日本語 file", []string{"docs/*"}, nil, true, false},
		{"traversal", "docs/../secret", []string{"**"}, nil, false, true},
		{"absolute", "C:/secret", []string{"**"}, nil, false, true},
		{"backslash", `docs\secret`, []string{"**"}, nil, false, true},
		{"invalid later allow", "safe", []string{"**", "../bad"}, nil, false, true},
		{"invalid later deny", "safe", []string{"**"}, []string{"safe", "a**"}, false, true},
		{"invalid deny without allow", "safe", nil, []string{"/bad"}, false, true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := PathAllowed(tt.path, tt.allowed, tt.denied)
			if got != tt.want || (err != nil) != tt.invalid {
				t.Fatalf("PathAllowed = %v, %v; want allowed=%v invalid=%v", got, err, tt.want, tt.invalid)
			}
		})
	}
}
