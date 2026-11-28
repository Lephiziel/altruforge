package store

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

func openTestStore(t *testing.T, path string) *Store {
	t.Helper()
	s, err := Open(path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := s.Close(); err != nil {
			t.Errorf("close store: %v", err)
		}
	})
	return s
}

func TestRunTransitionsAndDurableEvents(t *testing.T) {
	ctx := context.Background()
	s := openTestStore(t, filepath.Join(t.TempDir(), "runs.sqlite"))
	id := NewID()
	if len(id) != 36 || !runIDPattern.MatchString(id) {
		t.Fatalf("generated ID %q is invalid", id)
	}
	r, err := s.Create(ctx, id, 30*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	if r.State != Created {
		t.Fatalf("state=%s", r.State)
	}
	for i, to := range []State{Preflighting, Selecting, Claiming, Preparing, Implementing, Verifying, Implementing, Verifying, Publishing, AwaitingReview} {
		r, err = s.Transition(ctx, id, to, string(rune('a'+i)), "run.state_changed", json.RawMessage(`{"state":"`+string(to)+`"}`))
		if err != nil {
			t.Fatalf("transition to %s: %v", to, err)
		}
	}
	if r.Attempts != 2 {
		t.Fatalf("attempts=%d; want 2", r.Attempts)
	}
	if _, err = s.Transition(ctx, id, Implementing, "illegal", "run.state_changed", json.RawMessage(`{}`)); err == nil {
		t.Fatal("expected terminal transition rejection")
	}
	events, err := s.Events(ctx, id, 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 11 {
		t.Fatalf("events=%d; want 11", len(events))
	}
	for i, e := range events {
		if e.Sequence != int64(i+1) {
			t.Fatalf("event sequence[%d]=%d", i, e.Sequence)
		}
	}
}

func TestSpecialOutcomesAndPauseResume(t *testing.T) {
	cases := []struct {
		name string
		path []State
	}{{"no-work", []State{Preflighting, Selecting, NoWork}}, {"blocked", []State{Blocked}}, {"failure", []State{Failed}}, {"cancel", []State{Cancelled}}, {"pause", []State{Paused, Preflighting}}}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			s := openTestStore(t, filepath.Join(t.TempDir(), "runs.sqlite"))
			id := NewID()
			if _, err := s.Create(ctx, id, time.Minute); err != nil {
				t.Fatal(err)
			}
			from := Created
			for i, to := range tc.path {
				if from == Created && to != Preflighting && to != Blocked && to != Failed && to != Cancelled && to != Paused {
					t.Fatalf("bad test path")
				}
				_, err := s.Transition(ctx, id, to, string(rune('a'+i)), "run.state_changed", json.RawMessage(`{}`))
				if err != nil {
					t.Fatalf("%s -> %s: %v", from, to, err)
				}
				from = to
			}
		})
	}
}

func TestEffectiveAttemptLimitIsDurableAndEnforced(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "attempt-limit.sqlite")
	s := openTestStore(t, path)
	id := NewID()
	r, err := s.CreateWithLimits(ctx, id, time.Minute, 1)
	if err != nil {
		t.Fatal(err)
	}
	if r.MaxAttempts != 1 {
		t.Fatalf("max attempts=%d; want 1", r.MaxAttempts)
	}
	for i, to := range []State{Preflighting, Selecting, Claiming, Preparing, Implementing, Verifying} {
		if _, err := s.Transition(ctx, id, to, "first-"+string(rune('a'+i)), "run.state_changed", json.RawMessage(`{"state":"`+string(to)+`"}`)); err != nil {
			t.Fatalf("transition to %s: %v", to, err)
		}
	}
	if _, err := s.Transition(ctx, id, Implementing, "over-budget", "run.state_changed", json.RawMessage(`{"state":"implementing"}`)); err == nil {
		t.Fatal("expected attempt-limit rejection")
	}
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	s = openTestStore(t, path)
	r, err = s.Get(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if r.State != Verifying || r.Attempts != 1 || r.MaxAttempts != 1 {
		t.Fatalf("run after rejected attempt: %+v", r)
	}
}

func TestCheckpointAndSideEffectIntentAreDurableAndIdempotent(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "state.sqlite")
	s := openTestStore(t, path)
	id := NewID()
	if _, err := s.Create(ctx, id, time.Minute); err != nil {
		t.Fatal(err)
	}
	if err := s.SaveCheckpoint(ctx, id, json.RawMessage(`{"phase":"before publish"}`), "checkpoint-1"); err != nil {
		t.Fatal(err)
	}
	payload := json.RawMessage(`{"result":"sha"}`)
	if err := s.BeginSideEffect(ctx, id, "publish-1", "draft_pr", payload); err != nil {
		t.Fatal(err)
	}
	if err := s.BeginSideEffect(ctx, id, "publish-1", "draft_pr", payload); err != nil {
		t.Fatal(err)
	}
	if err := s.BeginSideEffect(ctx, id, "publish-1", "draft_pr", json.RawMessage(`{"result":"other"}`)); err == nil {
		t.Fatal("expected reused identity mismatch")
	}
	if err := s.SetSideEffectStatus(ctx, id, "publish-1", "observed"); err != nil {
		t.Fatal(err)
	}
	if err := s.SetSideEffectStatus(ctx, id, "publish-1", "intent"); err == nil {
		t.Fatal("expected side-effect status downgrade rejection")
	}
	effects, err := s.SideEffects(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if len(effects) != 1 || effects[0].Status != "observed" {
		t.Fatalf("side effects=%+v", effects)
	}
	if err := s.RecordElapsed(ctx, id, 7*time.Second); err != nil {
		t.Fatal(err)
	}
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	s = openTestStore(t, path)
	r, err := s.Get(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if string(r.Checkpoint) != `{"phase":"before publish"}` || r.Elapsed != 7*time.Second {
		t.Fatalf("reopened run=%+v", r)
	}
	events, err := s.Events(ctx, id, 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 2 || events[1].Type != "checkpoint.saved" {
		t.Fatalf("events=%+v", events)
	}
}

func TestEventReplayAndSensitiveFields(t *testing.T) {
	ctx := context.Background()
	s := openTestStore(t, filepath.Join(t.TempDir(), "replay.sqlite"))
	id := NewID()
	if _, err := s.Create(ctx, id, time.Minute); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 2; i++ {
		r, err := s.Transition(ctx, id, Preflighting, "preflight-event", "run.state_changed", json.RawMessage(`{"state":"preflighting"}`))
		if err != nil {
			t.Fatal(err)
		}
		if r.State != Preflighting {
			t.Fatalf("replayed state=%s", r.State)
		}
	}
	events, err := s.Events(ctx, id, 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 2 || events[1].Sequence != 2 {
		t.Fatalf("replayed events=%+v", events)
	}
	if events[0].SchemaVersion != "0.1" {
		t.Fatalf("schema version=%q", events[0].SchemaVersion)
	}
	if _, err := s.Transition(ctx, id, Selecting, "bad-secret", "run.state_changed", json.RawMessage(`{"access_token":"sensitive"}`)); err == nil {
		t.Fatal("expected sensitive field rejection")
	}
	if err := s.SaveCheckpoint(ctx, id, json.RawMessage(`{"provider_session":"export"}`), "secret-checkpoint"); err == nil {
		t.Fatal("expected session field rejection")
	}
}

func TestCommittedStateSurvivesForcedProcessExit(t *testing.T) {
	if os.Getenv("ALTRUFORGE_STORE_CRASH_HELPER") == "1" {
		path := os.Getenv("ALTRUFORGE_STORE_PATH")
		s, err := Open(path)
		if err != nil {
			os.Exit(10)
		}
		ctx := context.Background()
		id := "run_0123456789abcdef0123456789abcdef"
		if _, err = s.Create(ctx, id, time.Minute); err != nil {
			os.Exit(11)
		}
		if _, err = s.Transition(ctx, id, Preflighting, "event-1", "run.state_changed", json.RawMessage(`{"state":"preflighting"}`)); err != nil {
			os.Exit(12)
		}
		tx, err := s.db.BeginTx(ctx, nil)
		if err != nil {
			os.Exit(13)
		}
		if _, err = tx.ExecContext(ctx, `UPDATE runs SET state='awaiting_review' WHERE id=?`, id); err != nil {
			os.Exit(14)
		}
		// The apparent success is deliberately left uncommitted when the process exits.
		os.Exit(23)
	}
	path := filepath.Join(t.TempDir(), "crash.sqlite")
	cmd := exec.Command(os.Args[0], "-test.run=^TestCommittedStateSurvivesForcedProcessExit$")
	cmd.Env = append(os.Environ(), "ALTRUFORGE_STORE_CRASH_HELPER=1", "ALTRUFORGE_STORE_PATH="+path)
	err := cmd.Run()
	var exit *exec.ExitError
	if !errors.As(err, &exit) || exit.ExitCode() != 23 {
		t.Fatalf("child exit=%v; want intentional exit 23", err)
	}
	s := openTestStore(t, path)
	r, err := s.Get(context.Background(), "run_0123456789abcdef0123456789abcdef")
	if err != nil {
		t.Fatal(err)
	}
	if r.State != Preflighting {
		t.Fatalf("recovered state=%s", r.State)
	}
	events, err := s.Events(context.Background(), r.ID, 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 2 || events[0].Sequence != 1 || events[1].Sequence != 2 {
		t.Fatalf("recovered events=%+v", events)
	}
	n, err := s.RecoverInterrupted(context.Background(), "recovery-1")
	if err != nil {
		t.Fatal(err)
	}
	if n != 1 {
		t.Fatalf("recovered runs=%d; want 1", n)
	}
	r, err = s.Get(context.Background(), r.ID)
	if err != nil {
		t.Fatal(err)
	}
	if r.State != Paused {
		t.Fatalf("interrupted run state=%s; want paused", r.State)
	}
	if n, err = s.RecoverInterrupted(context.Background(), "recovery-1"); err != nil || n != 0 {
		t.Fatalf("idempotent recovery=(%d,%v); want (0,nil)", n, err)
	}
}

func TestMigrationAndCorruptionFailures(t *testing.T) {
	t.Run("newer schema", func(t *testing.T) {
		path := filepath.Join(t.TempDir(), "future.sqlite")
		s := openTestStore(t, path)
		if _, err := s.db.Exec(`PRAGMA user_version=99`); err != nil {
			t.Fatal(err)
		}
		s.Close()
		if _, err := Open(path); err == nil {
			t.Fatal("expected newer schema rejection")
		}
	})
	t.Run("corrupt file", func(t *testing.T) {
		path := filepath.Join(t.TempDir(), "corrupt.sqlite")
		if err := os.WriteFile(path, []byte("not a sqlite database"), 0o600); err != nil {
			t.Fatal(err)
		}
		if _, err := Open(path); err == nil {
			t.Fatal("expected corruption error")
		}
	})
	t.Run("incomplete versioned schema", func(t *testing.T) {
		path := filepath.Join(t.TempDir(), "incomplete.sqlite")
		db, err := sql.Open("sqlite", path)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := db.Exec(`PRAGMA user_version=1`); err != nil {
			t.Fatal(err)
		}
		if err := db.Close(); err != nil {
			t.Fatal(err)
		}
		if _, err := Open(path); err == nil {
			t.Fatal("expected incomplete schema rejection")
		}
	})
}

func TestEventSequenceAndElapsedAccumulation(t *testing.T) {
	ctx := context.Background()
	s := openTestStore(t, filepath.Join(t.TempDir(), "events.sqlite"))
	id := NewID()
	if _, err := s.Create(ctx, id, time.Minute); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 2; i++ {
		if err := s.SaveCheckpoint(ctx, id, json.RawMessage(`{}`), "checkpoint-"+string(rune('1'+i))); err != nil {
			t.Fatal(err)
		}
	}
	if err := s.RecordElapsed(ctx, id, 3*time.Second); err != nil {
		t.Fatal(err)
	}
	if err := s.RecordElapsed(ctx, id, 4*time.Second); err != nil {
		t.Fatal(err)
	}
	r, err := s.Get(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if r.Elapsed != 7*time.Second {
		t.Fatalf("elapsed=%s", r.Elapsed)
	}
	events, err := s.Events(ctx, id, 2)
	if err != nil {
		t.Fatal(err)
	}
	if len(events) != 1 || events[0].Sequence != 3 {
		t.Fatalf("after sequence 1: %+v", events)
	}
}

func TestMonotonicActiveInterval(t *testing.T) {
	s := openTestStore(t, filepath.Join(t.TempDir(), "monotonic.sqlite"))
	ctx := context.Background()
	id := NewID()
	if _, err := s.Create(ctx, id, time.Minute); err != nil {
		t.Fatal(err)
	}
	started := StartActiveInterval()
	if err := s.StopActiveInterval(ctx, id, started); err != nil {
		t.Fatal(err)
	}
	r, err := s.Get(ctx, id)
	if err != nil {
		t.Fatal(err)
	}
	if r.Elapsed < 0 {
		t.Fatalf("elapsed=%s", r.Elapsed)
	}
}
