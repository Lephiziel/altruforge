package store

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	_ "modernc.org/sqlite"
)

const schemaVersion = 1

var runIDPattern = regexp.MustCompile(`^run_[0-9a-f]{32}$`)

type State string

const (
	Created        State = "created"
	Preflighting   State = "preflighting"
	Selecting      State = "selecting"
	Claiming       State = "claiming"
	Preparing      State = "preparing"
	Implementing   State = "implementing"
	Verifying      State = "verifying"
	Publishing     State = "publishing"
	AwaitingReview State = "awaiting_review"
	Paused         State = "paused"
	NoWork         State = "no_work"
	Blocked        State = "blocked"
	Failed         State = "failed"
	Cancelled      State = "cancelled"
)

type Run struct {
	ID             string
	State          State
	Attempts       int
	Elapsed        time.Duration
	RequestedLimit time.Duration
	Checkpoint     json.RawMessage
	CreatedAt      time.Time
	UpdatedAt      time.Time
}

type Event struct {
	SchemaVersion string          `json:"schema_version"`
	RunID         string          `json:"run_id"`
	Sequence      int64           `json:"sequence"`
	Timestamp     time.Time       `json:"timestamp"`
	Type          string          `json:"type"`
	Data          json.RawMessage `json:"data"`
}

type SideEffect struct {
	ID        string
	Kind      string
	Status    string
	Payload   json.RawMessage
	UpdatedAt time.Time
}

type Store struct{ db *sql.DB }

func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, fmt.Errorf("open run store: %w", err)
	}
	db.SetMaxOpenConns(1)
	if _, err = db.Exec(`PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;`); err != nil {
		db.Close()
		return nil, fmt.Errorf("configure run store: %w", err)
	}
	s := &Store{db: db}
	if err = s.migrate(context.Background()); err != nil {
		db.Close()
		return nil, err
	}
	if err = s.validateSchema(context.Background()); err != nil {
		db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) migrate(ctx context.Context) error {
	var version int
	if err := s.db.QueryRowContext(ctx, `PRAGMA user_version`).Scan(&version); err != nil {
		return fmt.Errorf("read run store schema version: %w", err)
	}
	if version > schemaVersion {
		return fmt.Errorf("run store schema version %d is newer than supported version %d", version, schemaVersion)
	}
	if version == schemaVersion {
		return nil
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin run store migration: %w", err)
	}
	defer tx.Rollback()
	if version != 0 {
		return fmt.Errorf("no migration path from run store schema version %d", version)
	}
	statements := []string{
		`CREATE TABLE runs (id TEXT PRIMARY KEY, state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0), elapsed_ns INTEGER NOT NULL DEFAULT 0 CHECK(elapsed_ns >= 0), requested_limit_ns INTEGER NOT NULL CHECK(requested_limit_ns > 0), checkpoint_json BLOB NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)`,
		`CREATE TABLE events (run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, sequence INTEGER NOT NULL CHECK(sequence > 0), event_id TEXT NOT NULL, timestamp TEXT NOT NULL, type TEXT NOT NULL, data_json BLOB NOT NULL, PRIMARY KEY(run_id, sequence), UNIQUE(run_id, event_id))`,
		`CREATE TABLE side_effects (run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE, effect_id TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('intent','observed','complete')), payload_json BLOB NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(run_id, effect_id))`,
		`PRAGMA user_version = 1`,
	}
	for _, q := range statements {
		if _, err := tx.ExecContext(ctx, q); err != nil {
			return fmt.Errorf("apply run store migration 1: %w", err)
		}
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit run store migration 1: %w", err)
	}
	return nil
}

func (s *Store) validateSchema(ctx context.Context) error {
	var result string
	if err := s.db.QueryRowContext(ctx, `PRAGMA quick_check`).Scan(&result); err != nil {
		return fmt.Errorf("check run store integrity: %w", err)
	}
	if result != "ok" {
		return fmt.Errorf("run store integrity check failed: %s", result)
	}
	var tables int
	if err := s.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('runs','events','side_effects')`).Scan(&tables); err != nil {
		return fmt.Errorf("check run store schema: %w", err)
	}
	if tables != 3 {
		return fmt.Errorf("run store schema is incomplete: found %d of 3 required tables", tables)
	}
	return nil
}

func NewID() string { return "run_" + strings.ReplaceAll(uuid.NewString(), "-", "") }

func (s *Store) Create(ctx context.Context, id string, limit time.Duration) (Run, error) {
	if !runIDPattern.MatchString(id) {
		return Run{}, errors.New("invalid run ID")
	}
	if limit <= 0 {
		return Run{}, errors.New("requested time limit must be positive")
	}
	now := time.Now().UTC()
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Run{}, err
	}
	defer tx.Rollback()
	if _, err = tx.ExecContext(ctx, `INSERT INTO runs(id,state,requested_limit_ns,created_at,updated_at) VALUES(?,?,?,?,?)`, id, Created, int64(limit), stamp(now), stamp(now)); err != nil {
		return Run{}, fmt.Errorf("create run: %w", err)
	}
	if err = appendEvent(ctx, tx, id, "run.created", "run.state_changed", json.RawMessage(`{"state":"created"}`), now); err != nil {
		return Run{}, err
	}
	if err = tx.Commit(); err != nil {
		return Run{}, fmt.Errorf("commit run creation: %w", err)
	}
	return s.Get(ctx, id)
}

func (s *Store) Get(ctx context.Context, id string) (Run, error) {
	var r Run
	var checkpoint []byte
	var created, updated string
	var elapsed, limit int64
	err := s.db.QueryRowContext(ctx, `SELECT id,state,attempts,elapsed_ns,requested_limit_ns,checkpoint_json,created_at,updated_at FROM runs WHERE id=?`, id).Scan(&r.ID, &r.State, &r.Attempts, &elapsed, &limit, &checkpoint, &created, &updated)
	if err != nil {
		return Run{}, err
	}
	r.Elapsed = time.Duration(elapsed)
	r.RequestedLimit = time.Duration(limit)
	r.Checkpoint = append(json.RawMessage(nil), checkpoint...)
	r.CreatedAt, _ = time.Parse(time.RFC3339Nano, created)
	r.UpdatedAt, _ = time.Parse(time.RFC3339Nano, updated)
	return r, nil
}

func (s *Store) Transition(ctx context.Context, id string, to State, eventID, eventType string, data json.RawMessage) (Run, error) {
	if !validState(to) {
		return Run{}, fmt.Errorf("unknown run state %q", to)
	}
	if eventID == "" || eventType == "" {
		return Run{}, errors.New("event identity and type are required")
	}
	if !validEventType(eventType) {
		return Run{}, fmt.Errorf("unknown event type %q", eventType)
	}
	if !safeObject(data) {
		return Run{}, errors.New("event data must be a safe JSON object without credential/session fields")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return Run{}, err
	}
	defer tx.Rollback()
	var prior int
	if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM events WHERE run_id=? AND event_id=?`, id, eventID).Scan(&prior); err != nil {
		return Run{}, err
	}
	if prior > 0 {
		r, err := getTx(ctx, tx, id)
		if err != nil {
			return Run{}, err
		}
		if err = tx.Commit(); err != nil {
			return Run{}, err
		}
		return r, nil
	}
	r, err := getTx(ctx, tx, id)
	if err != nil {
		return Run{}, err
	}
	if !canTransition(r.State, to) {
		return Run{}, fmt.Errorf("invalid run transition %s -> %s", r.State, to)
	}
	now := time.Now().UTC()
	if to == Implementing && r.State != Implementing {
		r.Attempts++
	}
	if _, err = tx.ExecContext(ctx, `UPDATE runs SET state=?,attempts=?,updated_at=? WHERE id=?`, to, r.Attempts, stamp(now), id); err != nil {
		return Run{}, err
	}
	if err = appendEvent(ctx, tx, id, eventID, eventType, data, now); err != nil {
		return Run{}, err
	}
	if err = tx.Commit(); err != nil {
		return Run{}, err
	}
	return s.Get(ctx, id)
}

func (s *Store) SaveCheckpoint(ctx context.Context, id string, checkpoint json.RawMessage, eventID string) error {
	if eventID == "" {
		return errors.New("checkpoint event identity is required")
	}
	if !safeObject(checkpoint) {
		return errors.New("checkpoint must be a safe JSON object without credential/session fields")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var prior int
	if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM events WHERE run_id=? AND event_id=?`, id, eventID).Scan(&prior); err != nil {
		return err
	}
	if prior > 0 {
		return nil
	}
	if _, err = tx.ExecContext(ctx, `UPDATE runs SET checkpoint_json=?,updated_at=? WHERE id=?`, []byte(checkpoint), stamp(time.Now().UTC()), id); err != nil {
		return err
	}
	res, err := tx.ExecContext(ctx, `INSERT INTO events(run_id,sequence,event_id,timestamp,type,data_json) SELECT ?,COALESCE(MAX(sequence),0)+1,?,?,?,? FROM events WHERE run_id=?`, id, eventID, stamp(time.Now().UTC()), "checkpoint.saved", []byte(`{"saved":true}`), id)
	if err != nil {
		return fmt.Errorf("persist checkpoint event: %w", err)
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("run not found")
	}
	return tx.Commit()
}

// BeginSideEffect durably records intent before a caller performs an external operation.
func (s *Store) BeginSideEffect(ctx context.Context, id, effectID, kind string, payload json.RawMessage) error {
	if effectID == "" || kind == "" || !safeObject(payload) {
		return errors.New("side effect requires identity, kind, and safe JSON object payload")
	}
	_, err := s.db.ExecContext(ctx, `INSERT INTO side_effects(run_id,effect_id,kind,status,payload_json,updated_at) VALUES(?,?,?,'intent',?,?) ON CONFLICT(run_id,effect_id) DO NOTHING`, id, effectID, kind, []byte(payload), stamp(time.Now().UTC()))
	if err != nil {
		return fmt.Errorf("persist side-effect intent: %w", err)
	}
	var existingKind string
	var existingPayload []byte
	if err = s.db.QueryRowContext(ctx, `SELECT kind,payload_json FROM side_effects WHERE run_id=? AND effect_id=?`, id, effectID).Scan(&existingKind, &existingPayload); err != nil {
		return err
	}
	if existingKind != kind || string(existingPayload) != string(payload) {
		return errors.New("side-effect identity already used with different content")
	}
	return nil
}

func (s *Store) SetSideEffectStatus(ctx context.Context, id, effectID, status string) error {
	if status != "observed" && status != "complete" {
		return errors.New("side-effect status must be observed or complete")
	}
	res, err := s.db.ExecContext(ctx, `UPDATE side_effects SET status=?,updated_at=? WHERE run_id=? AND effect_id=? AND (status=? OR (status='intent' AND ? IN ('observed','complete')) OR (status='observed' AND ?='complete'))`, status, stamp(time.Now().UTC()), id, effectID, status, status, status)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return sql.ErrNoRows
	}
	return nil
}

func (s *Store) SideEffects(ctx context.Context, runID string) ([]SideEffect, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT effect_id,kind,status,payload_json,updated_at FROM side_effects WHERE run_id=? ORDER BY effect_id`, runID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var effects []SideEffect
	for rows.Next() {
		var effect SideEffect
		var payload []byte
		var updated string
		if err := rows.Scan(&effect.ID, &effect.Kind, &effect.Status, &payload, &updated); err != nil {
			return nil, err
		}
		effect.Payload = append(json.RawMessage(nil), payload...)
		effect.UpdatedAt, _ = time.Parse(time.RFC3339Nano, updated)
		effects = append(effects, effect)
	}
	return effects, rows.Err()
}

func (s *Store) Events(ctx context.Context, id string, after int64) ([]Event, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT run_id,sequence,timestamp,type,data_json FROM events WHERE run_id=? AND sequence>? ORDER BY sequence`, id, after)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Event
	for rows.Next() {
		var e Event
		var ts string
		var d []byte
		if err := rows.Scan(&e.RunID, &e.Sequence, &ts, &e.Type, &d); err != nil {
			return nil, err
		}
		e.SchemaVersion = "0.1"
		e.Timestamp, _ = time.Parse(time.RFC3339Nano, ts)
		e.Data = append(json.RawMessage(nil), d...)
		out = append(out, e)
	}
	return out, rows.Err()
}

func (s *Store) RecordElapsed(ctx context.Context, id string, d time.Duration) error {
	if d < 0 {
		return errors.New("elapsed duration cannot be negative")
	}
	res, err := s.db.ExecContext(ctx, `UPDATE runs SET elapsed_ns=elapsed_ns+?,updated_at=? WHERE id=?`, int64(d), stamp(time.Now().UTC()), id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return sql.ErrNoRows
	}
	return nil
}

// StartActiveInterval captures a monotonic clock reading for one in-process interval.
func StartActiveInterval() time.Time { return time.Now() }

// StopActiveInterval adds an in-process monotonic interval to the durable elapsed total.
// Callers must stop and persist before explicit pause/resume. An uncommitted interval is
// intentionally not reconstructed from wall-clock timestamps after a process crash.
func (s *Store) StopActiveInterval(ctx context.Context, id string, started time.Time) error {
	if started.IsZero() {
		return errors.New("active interval start is required")
	}
	return s.RecordElapsed(ctx, id, time.Since(started))
}

// RecoverInterrupted makes unfinished work explicitly resumable without claiming it succeeded.
// The caller supplies an event ID to make recovery itself safe to retry.
func (s *Store) RecoverInterrupted(ctx context.Context, eventID string) (int, error) {
	if eventID == "" {
		return 0, errors.New("recovery event identity is required")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	rows, err := tx.QueryContext(ctx, `SELECT id,state FROM runs WHERE state IN ('created','preflighting','selecting','claiming','preparing','implementing','verifying','publishing') ORDER BY id`)
	if err != nil {
		return 0, err
	}
	type unfinished struct {
		id    string
		state State
	}
	var runs []unfinished
	for rows.Next() {
		var r unfinished
		if err := rows.Scan(&r.id, &r.state); err != nil {
			rows.Close()
			return 0, err
		}
		runs = append(runs, r)
	}
	if err := rows.Err(); err != nil {
		rows.Close()
		return 0, err
	}
	rows.Close()
	count := 0
	now := time.Now().UTC()
	for _, r := range runs {
		key := eventID + ":" + r.id
		var exists int
		if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM events WHERE run_id=? AND event_id=?`, r.id, key).Scan(&exists); err != nil {
			return 0, err
		}
		if exists > 0 {
			continue
		}
		data, _ := json.Marshal(map[string]string{"state": "paused", "recovered_from": string(r.state)})
		if _, err := tx.ExecContext(ctx, `UPDATE runs SET state='paused',updated_at=? WHERE id=?`, stamp(now), r.id); err != nil {
			return 0, err
		}
		if err := appendEvent(ctx, tx, r.id, key, "run.state_changed", data, now); err != nil {
			return 0, err
		}
		count++
	}
	if err := tx.Commit(); err != nil {
		return 0, err
	}
	return count, nil
}

func appendEvent(ctx context.Context, tx *sql.Tx, id, eventID, eventType string, data json.RawMessage, now time.Time) error {
	if !safeObject(data) {
		return errors.New("event data must be a safe JSON object")
	}
	var prior int
	if err := tx.QueryRowContext(ctx, `SELECT COUNT(*) FROM events WHERE run_id=? AND event_id=?`, id, eventID).Scan(&prior); err != nil {
		return err
	}
	if prior > 0 {
		return nil
	}
	var seq int64
	if err := tx.QueryRowContext(ctx, `SELECT COALESCE(MAX(sequence),0)+1 FROM events WHERE run_id=?`, id).Scan(&seq); err != nil {
		return err
	}
	_, err := tx.ExecContext(ctx, `INSERT INTO events(run_id,sequence,event_id,timestamp,type,data_json) VALUES(?,?,?,?,?,?)`, id, seq, eventID, stamp(now), eventType, []byte(data))
	if err != nil {
		if isUnique(err) {
			return nil
		}
		return fmt.Errorf("append event: %w", err)
	}
	return nil
}

func getTx(ctx context.Context, tx *sql.Tx, id string) (Run, error) {
	var r Run
	var elapsed, limit int64
	var b []byte
	var c, u string
	err := tx.QueryRowContext(ctx, `SELECT id,state,attempts,elapsed_ns,requested_limit_ns,checkpoint_json,created_at,updated_at FROM runs WHERE id=?`, id).Scan(&r.ID, &r.State, &r.Attempts, &elapsed, &limit, &b, &c, &u)
	if err != nil {
		return Run{}, err
	}
	r.Elapsed = time.Duration(elapsed)
	r.RequestedLimit = time.Duration(limit)
	r.Checkpoint = b
	return r, nil
}
func stamp(t time.Time) string { return t.UTC().Format(time.RFC3339Nano) }
func validState(s State) bool {
	switch s {
	case Created, Preflighting, Selecting, Claiming, Preparing, Implementing, Verifying, Publishing, AwaitingReview, Paused, NoWork, Blocked, Failed, Cancelled:
		return true
	}
	return false
}

func validEventType(t string) bool {
	switch t {
	case "run.state_changed", "task.selected", "agent.message", "check.completed", "budget.notice", "checkpoint.saved", "publication.created", "run.error":
		return true
	}
	return false
}
func canTransition(from, to State) bool {
	if from == to {
		return true
	}
	if from == AwaitingReview || from == NoWork || from == Blocked || from == Failed || from == Cancelled {
		return false
	}
	if to == Blocked || to == Failed || to == Cancelled || to == Paused {
		return true
	}
	if from == Paused {
		return to == Preflighting
	}
	switch from {
	case Created:
		return to == Preflighting
	case Preflighting:
		return to == Selecting
	case Selecting:
		return to == Claiming || to == NoWork
	case Claiming:
		return to == Preparing || to == Selecting
	case Preparing:
		return to == Implementing
	case Implementing:
		return to == Verifying
	case Verifying:
		return to == Implementing || to == Publishing
	case Publishing:
		return to == AwaitingReview
	}
	return false
}

// SQLite reports unique conflicts consistently for the pinned modernc driver.
func isUnique(err error) bool {
	return err != nil && (contains(err.Error(), "UNIQUE constraint failed") || contains(err.Error(), "unique constraint"))
}
func contains(s, sub string) bool {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}

func safeObject(raw json.RawMessage) bool {
	var value any
	if !json.Valid(raw) || json.Unmarshal(raw, &value) != nil {
		return false
	}
	object, ok := value.(map[string]any)
	return ok && safeValue(object)
}

func safeValue(value any) bool {
	switch v := value.(type) {
	case map[string]any:
		for key, child := range v {
			normalized := strings.ToLower(strings.ReplaceAll(strings.ReplaceAll(key, "-", "_"), " ", "_"))
			for _, sensitive := range []string{"credential", "authorization", "password", "secret", "token", "session", "cookie", "api_key"} {
				if strings.Contains(normalized, sensitive) {
					return false
				}
			}
			if !safeValue(child) {
				return false
			}
		}
	case []any:
		for _, child := range v {
			if !safeValue(child) {
				return false
			}
		}
	}
	return true
}
