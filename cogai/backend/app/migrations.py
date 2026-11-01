"""Additive SQLite migrations. Never rebuild or discard the legacy encrypted records."""

MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL,
        consent TEXT NOT NULL, expires REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
        kind TEXT NOT NULL, payload BLOB NOT NULL, created REAL NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS owned_records ON records(session_id, created);
    """,
    """
    ALTER TABLE sessions ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;
    CREATE TABLE accounts (
        owner_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
        alias TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user', retention_days INTEGER NOT NULL DEFAULT 30,
        created REAL NOT NULL
    );
    CREATE TABLE auth_sessions (
        token_hash TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES accounts(owner_id) ON DELETE CASCADE,
        expires REAL NOT NULL, created REAL NOT NULL
    );
    CREATE TABLE documents (
        owner_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        key TEXT NOT NULL, kind TEXT NOT NULL, payload BLOB NOT NULL,
        created REAL NOT NULL, updated REAL NOT NULL, PRIMARY KEY(owner_id,key)
    );
    CREATE TABLE audit (
        id INTEGER PRIMARY KEY, owner_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
        action TEXT NOT NULL, created REAL NOT NULL
    );
    CREATE TABLE consent_events (
        id INTEGER PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        revision INTEGER NOT NULL, choices TEXT NOT NULL, created REAL NOT NULL
    );
    CREATE TABLE referrals (
        id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        assigned_to TEXT REFERENCES accounts(owner_id) ON DELETE SET NULL,
        status TEXT NOT NULL, summary BLOB NOT NULL, created REAL NOT NULL, updated REAL NOT NULL
    );
    """,
    """
    -- Organisation group (company, union, school) for anonymous aggregate reports only.
    ALTER TABLE accounts ADD COLUMN cohort TEXT;
    """,
]


def migrate(db):
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version > len(MIGRATIONS):
        raise RuntimeError('Database schema is newer than this application; use its matching release.')
    for index in range(version, len(MIGRATIONS)):
        # executescript commits any preceding transaction. Explicit transaction covers
        # each complete migration including user_version; failed scripts roll back.
        try:
            db.executescript(f'BEGIN IMMEDIATE;\n{MIGRATIONS[index]}\nPRAGMA user_version={index+1};\nCOMMIT;')
        except Exception:
            db.rollback()
            raise
