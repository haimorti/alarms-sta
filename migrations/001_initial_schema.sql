CREATE TABLE IF NOT EXISTS raw_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at TEXT NOT NULL,
    source_payload TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_event_id TEXT,
    title TEXT,
    cat TEXT,
    desc TEXT,
    payload_hash TEXT NOT NULL,
    http_status INTEGER,
    response_latency_ms REAL,
    archive_path TEXT,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    is_duplicate INTEGER NOT NULL DEFAULT 0,
    duplicate_of_raw_event_id INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS normalized_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_event_id INTEGER NOT NULL,
    normalized_type TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    source_event_id TEXT,
    confidence_in_classification REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(raw_event_id) REFERENCES raw_events(id)
);

CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_he TEXT NOT NULL UNIQUE,
    name_en TEXT,
    aliases TEXT,
    lat REAL,
    lon REAL,
    region TEXT,
    district TEXT,
    geometry TEXT,
    source_dataset TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settlement_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    settlement_id INTEGER,
    alias TEXT NOT NULL UNIQUE,
    alias_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(settlement_id) REFERENCES settlements(id)
);

CREATE TABLE IF NOT EXISTS event_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_event_id INTEGER NOT NULL,
    location_name_raw TEXT NOT NULL,
    location_name_normalized TEXT,
    settlement_id INTEGER,
    lat REAL,
    lon REAL,
    resolution_confidence REAL NOT NULL DEFAULT 0,
    resolution_notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(normalized_event_id) REFERENCES normalized_events(id),
    FOREIGN KEY(settlement_id) REFERENCES settlements(id)
);

CREATE TABLE IF NOT EXISTS event_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_event_id INTEGER,
    cluster_start_time TEXT,
    cluster_end_time TEXT,
    cluster_type TEXT,
    matching_method TEXT,
    confidence_score REAL NOT NULL DEFAULT 0,
    explanation TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(trigger_event_id) REFERENCES normalized_events(id)
);

CREATE TABLE IF NOT EXISTS cluster_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    normalized_event_id INTEGER NOT NULL,
    role_in_cluster TEXT NOT NULL,
    membership_score REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cluster_id) REFERENCES event_clusters(id),
    FOREIGN KEY(normalized_event_id) REFERENCES normalized_events(id)
);

CREATE TABLE IF NOT EXISTS probability_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    settlement_id INTEGER NOT NULL,
    spatial_score REAL NOT NULL,
    spatial_label TEXT NOT NULL,
    spatial_confidence REAL NOT NULL,
    spatial_confidence_label TEXT NOT NULL,
    spatial_explanation TEXT NOT NULL,
    historical_score REAL NOT NULL,
    historical_label TEXT NOT NULL,
    historical_confidence REAL NOT NULL,
    historical_confidence_label TEXT NOT NULL,
    historical_explanation TEXT NOT NULL,
    weighted_score REAL NOT NULL,
    weighted_label TEXT NOT NULL,
    weighted_confidence REAL NOT NULL,
    weighted_confidence_label TEXT NOT NULL,
    weighted_explanation TEXT NOT NULL,
    weighting_profile TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cluster_id) REFERENCES event_clusters(id),
    FOREIGN KEY(settlement_id) REFERENCES settlements(id)
);

CREATE TABLE IF NOT EXISTS risk_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    normalized_event_id INTEGER,
    phase_index INTEGER NOT NULL,
    phase_label TEXT NOT NULL,
    window_started_at TEXT NOT NULL,
    window_ended_at TEXT,
    geometry_kind TEXT NOT NULL,
    geometry_payload TEXT NOT NULL,
    centroid_lat REAL,
    centroid_lon REAL,
    area_scale REAL,
    trajectory_confidence REAL NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cluster_id) REFERENCES event_clusters(id),
    FOREIGN KEY(normalized_event_id) REFERENCES normalized_events(id)
);

CREATE INDEX IF NOT EXISTS idx_raw_events_payload_hash
ON raw_events(payload_hash);
