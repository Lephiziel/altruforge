// Package manifest provides lexical helpers for repository manifest paths.
package manifest

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

// ValidatePath accepts nonempty repository-relative forward-slash paths.
// It rejects ambiguous components instead of cleaning them. Colons are rejected
// throughout to exclude Windows drive and alternate-stream forms on every host.
// Validation is lexical: it does not establish filesystem or symlink confinement.
func ValidatePath(path string) error {
	if path == "" || !utf8.ValidString(path) || strings.ContainsAny(path, "\\:\x00") {
		return fmt.Errorf("invalid repository-relative path %q", path)
	}
	for _, segment := range strings.Split(path, "/") {
		if segment == "" || segment == "." || segment == ".." {
			return fmt.Errorf("invalid path component in %q", path)
		}
	}
	return nil
}

// ValidatePattern applies path validation and requires ** to be a whole segment.
// Only * and ** are operators; question marks, brackets, and braces are literals.
func ValidatePattern(pattern string) error {
	if err := ValidatePath(pattern); err != nil {
		return err
	}
	for _, segment := range strings.Split(pattern, "/") {
		if segment != "**" && strings.Contains(segment, "**") {
			return fmt.Errorf("double star must occupy a whole segment: %q", pattern)
		}
	}
	return nil
}

// MatchPath matches an entire validated path. A * matches zero or more bytes
// within one segment; a whole-segment ** matches zero or more complete segments.
// Thus docs/** matches docs and docs/a/b, and **/a matches a and x/y/a.
// Matching is case-sensitive and does not normalize Unicode or separators.
func MatchPath(pattern, path string) (bool, error) {
	if err := ValidatePattern(pattern); err != nil {
		return false, err
	}
	if err := ValidatePath(path); err != nil {
		return false, err
	}
	return matchPath(pattern, path), nil
}

func matchPath(pattern, path string) bool {
	parts := strings.Split(path, "/")
	matched := make([]bool, len(parts)+1)
	matched[0] = true
	for _, segment := range strings.Split(pattern, "/") {
		next := make([]bool, len(parts)+1)
		if segment == "**" {
			next[0] = matched[0]
			for j := 1; j <= len(parts); j++ {
				next[j] = matched[j] || next[j-1]
			}
		} else {
			for j := 1; j <= len(parts); j++ {
				next[j] = matched[j-1] && matchSegment(segment, parts[j-1])
			}
		}
		matched = next
	}
	return matched[len(parts)]
}

func matchSegment(pattern, segment string) bool {
	matched := make([]bool, len(segment)+1)
	matched[0] = true
	for i := 0; i < len(pattern); i++ {
		next := make([]bool, len(segment)+1)
		if pattern[i] == '*' {
			next[0] = matched[0]
			for j := 1; j <= len(segment); j++ {
				next[j] = matched[j] || next[j-1]
			}
		} else {
			for j := 1; j <= len(segment); j++ {
				next[j] = matched[j-1] && pattern[i] == segment[j-1]
			}
		}
		matched = next
	}
	return matched[len(segment)]
}

// PathAllowed requires an allow match and no deny match. Every pattern is
// validated before evaluating matches, including patterns after an early match.
// Invalid input always returns false with an error. Callers must supply protected
// path denials; this helper does not define or integrate runtime policy.
func PathAllowed(path string, allowed, denied []string) (bool, error) {
	if err := ValidatePath(path); err != nil {
		return false, err
	}
	for _, patterns := range [][]string{allowed, denied} {
		for _, pattern := range patterns {
			if err := ValidatePattern(pattern); err != nil {
				return false, err
			}
		}
	}
	for _, pattern := range denied {
		if matchPath(pattern, path) {
			return false, nil
		}
	}
	for _, pattern := range allowed {
		if matchPath(pattern, path) {
			return true, nil
		}
	}
	return false, nil
}
