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
