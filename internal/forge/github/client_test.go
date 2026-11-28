package github

import (
	"context"
	"errors"
	"reflect"
	"strings"
	"testing"
)

type call struct {
	name string
	args []string
}
type fakeRunner struct {
	calls   []call
	results [][]byte
	errs    []error
}

func (f *fakeRunner) Run(_ context.Context, name string, args ...string) ([]byte, error) {
	f.calls = append(f.calls, call{name, append([]string(nil), args...)})
	i := len(f.calls) - 1
	if i < len(f.errs) && f.errs[i] != nil {
		return nil, f.errs[i]
	}
	if i < len(f.results) {
		return f.results[i], nil
	}
	return nil, nil
}

func TestAccountUsesSupportedGHAuthWithoutPrintingCredential(t *testing.T) {
	f := &fakeRunner{results: [][]byte{[]byte("authenticated\n"), []byte("contributor\n")}}
	got, err := (Client{Runner: f}).Account(context.Background())
	if err != nil || got != "contributor" {
		t.Fatalf("Account() = %q, %v", got, err)
	}
	want := []call{{"gh", []string{"auth", "status", "--hostname", "github.com"}}, {"gh", []string{"api", "user", "--jq", ".login"}}}
	if !reflect.DeepEqual(f.calls, want) {
		t.Fatalf("calls = %#v", f.calls)
	}
}

func TestAccountRedactsFailureOutput(t *testing.T) {
	f := &fakeRunner{errs: []error{errors.New("token=secret")}}
	_, err := (Client{Runner: f}).Account(context.Background())
	if err == nil || err.Error() != string(AuthenticationRevoked) {
		t.Fatalf("error = %v", err)
	}
}

func TestPublicRepositoryRejectsPrivateTarget(t *testing.T) {
	f := &fakeRunner{results: [][]byte{[]byte(`{"full_name":"team/private","visibility":"private","clone_url":"https://github.com/team/private.git","default_branch":"main"}`)}}
	_, err := (Client{Runner: f}).PublicRepository(context.Background(), "team/private")
	if err == nil {
		t.Fatal("private repository was accepted")
	}
}

func TestSlugRejectsArguments(t *testing.T) {
	for _, slug := range []string{"owner/repo --help", "owner/../repo", "owner", "owner/repo\n"} {
		if validSlug(slug) {
			t.Errorf("accepted %q", slug)
		}
	}
}

func TestForkReusesExistingForkWithoutCreateRetry(t *testing.T) {
	existing := []byte(`{"full_name":"user/repo","fork":true}`)
	f := &fakeRunner{results: [][]byte{existing}}
	_, err := (Client{Runner: f}).Fork(context.Background(), Repository{FullName: "upstream/repo"}, "user")
	var classified *Error
	if !errors.As(err, &classified) || classified.Class != ExistingFork {
		t.Fatalf("error = %v", err)
	}
	if len(f.calls) != 1 {
		t.Fatalf("unexpected calls after existing fork: %#v", f.calls)
	}
}

func TestFailuresAreClassifiedAndRedacted(t *testing.T) {
	for _, tc := range []struct {
		text string
		want Failure
	}{{"HTTP 403 permission denied token=secret", MissingAccess}, {"connection timed out", NetworkFailure}, {"HTTP 401 bad credentials", AuthenticationRevoked}} {
		err := classify(errors.New(tc.text), false)
		if err.Error() != string(tc.want) || strings.Contains(err.Error(), "secret") {
			t.Errorf("classify(%q) = %v", tc.text, err)
		}
	}
}
