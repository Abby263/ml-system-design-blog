CREATE SEQUENCE IF NOT EXISTS url_id_seq START WITH 56800235584;

CREATE TABLE IF NOT EXISTS short_links (
    id BIGINT PRIMARY KEY,
    short_code VARCHAR(32) NOT NULL UNIQUE,
    target_url TEXT NOT NULL CHECK (length(target_url) <= 2048),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CHECK (expires_at IS NULL OR expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS short_links_expiry_idx
    ON short_links (expires_at)
    WHERE expires_at IS NOT NULL AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS daily_clicks (
    short_code VARCHAR(32) NOT NULL,
    click_date DATE NOT NULL,
    clicks BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (short_code, click_date)
);
