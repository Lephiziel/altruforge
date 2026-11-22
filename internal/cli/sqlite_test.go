package cli

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"

	_ "modernc.org/sqlite"
)

func TestSQLitePersistence(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "Unicode path 日本語")
	if err := os.Mkdir(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "bootstrap database.sqlite")
	open := func() *sql.DB {
		t.Helper()
		db, err := sql.Open("sqlite", path)
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(func() {
			if err := db.Close(); err != nil {
				t.Errorf("close database: %v", err)
			}
		})
		return db
	}

	db := open()
	if _, err := db.Exec("CREATE TABLE bootstrap (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"); err != nil {
		t.Fatal(err)
	}
	const want = "persisted value 日本語"
	if _, err := db.Exec("INSERT INTO bootstrap (id, value) VALUES (?, ?)", 1, want); err != nil {
		t.Fatal(err)
	}
	verify := func(db *sql.DB) {
		t.Helper()
		var got string
		if err := db.QueryRow("SELECT value FROM bootstrap WHERE id = ?", 1).Scan(&got); err != nil {
			t.Fatal(err)
		}
		if got != want {
			t.Fatalf("value = %q; want %q", got, want)
		}
	}
	verify(db)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	verify(open())
}

func TestSQLiteTransactionPersistence(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "Unicode path 日本語")
	if err := os.Mkdir(dir, 0o700); err != nil {
		t.Fatalf("create database directory: %v", err)
	}
	path := filepath.Join(dir, "transaction database.sqlite")
	open := func() *sql.DB {
		t.Helper()
		db, err := sql.Open("sqlite", path)
		if err != nil {
			t.Fatalf("open database: %v", err)
		}
		t.Cleanup(func() {
			if err := db.Close(); err != nil {
				t.Errorf("close database: %v", err)
			}
		})
		return db
	}
	begin := func(db *sql.DB) *sql.Tx {
		t.Helper()
		tx, err := db.Begin()
		if err != nil {
			t.Fatalf("begin transaction: %v", err)
		}
		t.Cleanup(func() {
			if err := tx.Rollback(); err != nil && err != sql.ErrTxDone {
				t.Errorf("clean up transaction: %v", err)
			}
		})
		return tx
	}

	db := open()
	if _, err := db.Exec("CREATE TABLE transactions (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"); err != nil {
		t.Fatalf("create table: %v", err)
	}
	const rolledBackID = 11
	const committedID = 22
	const committedValue = "committed value"
	verifyRolledBack := func(db *sql.DB) {
		t.Helper()
		var value string
		err := db.QueryRow("SELECT value FROM transactions WHERE id = ?", rolledBackID).Scan(&value)
		if err != sql.ErrNoRows {
			t.Fatalf("rolled-back row lookup: value = %q, error = %v; want sql.ErrNoRows", value, err)
		}
	}

	rollbackTx := begin(db)
	if _, err := rollbackTx.Exec("INSERT INTO transactions (id, value) VALUES (?, ?)", rolledBackID, "rolled-back value"); err != nil {
		t.Fatalf("insert rollback row: %v", err)
	}
	if err := rollbackTx.Rollback(); err != nil {
		t.Fatalf("roll back transaction: %v", err)
	}
	verifyRolledBack(db)

	commitTx := begin(db)
	if _, err := commitTx.Exec("INSERT INTO transactions (id, value) VALUES (?, ?)", committedID, committedValue); err != nil {
		t.Fatalf("insert committed row: %v", err)
	}
	if err := commitTx.Commit(); err != nil {
		t.Fatalf("commit transaction: %v", err)
	}
	if err := db.Close(); err != nil {
		t.Fatalf("close database before reopening: %v", err)
	}

	reopened := open()
	var count int
	if err := reopened.QueryRow("SELECT COUNT(*) FROM transactions").Scan(&count); err != nil {
		t.Fatalf("count surviving rows: %v", err)
	}
	if count != 1 {
		t.Fatalf("surviving row count = %d; want 1", count)
	}
	var id int
	var value string
	if err := reopened.QueryRow("SELECT id, value FROM transactions").Scan(&id, &value); err != nil {
		t.Fatalf("read surviving row: %v", err)
	}
	if id != committedID || value != committedValue {
		t.Fatalf("surviving row = (%d, %q); want (%d, %q)", id, value, committedID, committedValue)
	}
	verifyRolledBack(reopened)
}
