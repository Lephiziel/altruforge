package cli

import (
	"bytes"
	"errors"
	"io"
	"strings"
	"testing"
)

type failingWriter struct {
	err error
}

func (w failingWriter) Write([]byte) (int, error) {
	return 0, w.err
}

func TestRootHelpPropagatesWriteError(t *testing.T) {
	failure := errors.New("help output failed")
	for _, args := range [][]string{nil, {"--help"}, {"-h"}} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			err := Execute(args, failingWriter{err: failure}, io.Discard)
			if !errors.Is(err, failure) {
				t.Fatalf("Execute(%q) = %v; want underlying writer failure", args, err)
			}
		})
	}
}

func TestRootHelp(t *testing.T) {
	for _, args := range [][]string{nil, {"--help"}, {"-h"}} {
		var output bytes.Buffer
		if err := Execute(args, &output, io.Discard); err != nil {
			t.Fatalf("Execute(%q): %v", args, err)
		}
		if !strings.Contains(output.String(), "Usage:") || !strings.Contains(output.String(), "altruforge") {
			t.Fatalf("Execute(%q) produced incomplete help: %q", args, output.String())
		}
	}
}

func TestUnsupportedCommandsFail(t *testing.T) {
	for _, arg := range []string{"unknown", "run", "login", "publish", "--unknown"} {
		if err := Execute([]string{arg}, io.Discard, io.Discard); err == nil {
			t.Errorf("Execute(%q) succeeded", arg)
		}
	}
}
