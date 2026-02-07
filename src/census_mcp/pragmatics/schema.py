"""SQLite schema for pragmatic context packs.

Schema defined in docs/design/pragmatics_vocabulary.md (normative).
"""

import sqlite3

SCHEMA_DDL = """
-- A piece of context
CREATE TABLE IF NOT EXISTS context (
    id INTEGER PRIMARY KEY,
    context_id TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    category TEXT,
    latitude TEXT NOT NULL CHECK (latitude IN ('none', 'narrow', 'wide', 'full')),
    context_text TEXT NOT NULL,
    triggers TEXT,  -- JSON array of trigger strings
    source TEXT     -- provenance JSON
);

-- Threads: how context connects
CREATE TABLE IF NOT EXISTS threads (
    from_context_id TEXT NOT NULL,
    to_context_id TEXT NOT NULL,
    edge_type TEXT NOT NULL CHECK (edge_type IN ('inherits', 'applies_to', 'relates_to')),
    PRIMARY KEY (from_context_id, to_context_id, edge_type)
);

-- Packs: domain collections
CREATE TABLE IF NOT EXISTS packs (
    pack_id TEXT PRIMARY KEY,
    pack_name TEXT NOT NULL,
    parent_pack TEXT,
    version TEXT NOT NULL,
    compiled_date TEXT NOT NULL
);

-- Which context belongs to which pack
CREATE TABLE IF NOT EXISTS pack_contents (
    pack_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    PRIMARY KEY (pack_id, context_id)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_context_domain ON context(domain);
CREATE INDEX IF NOT EXISTS idx_context_latitude ON context(latitude);
CREATE INDEX IF NOT EXISTS idx_threads_from ON threads(from_context_id);
CREATE INDEX IF NOT EXISTS idx_threads_to ON threads(to_context_id);
"""


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all schema tables and indexes.
    
    Args:
        conn: SQLite database connection
    """
    conn.executescript(SCHEMA_DDL)
    conn.commit()
