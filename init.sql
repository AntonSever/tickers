CREATE TABLE IF NOT EXISTS tickers (
    updated_at BIGINT NOT NULL,
    ticker_id BIGINT NOT NULL,
    price BIGINT NOT NULL
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS ticker_idx ON tickers (ticker_id, updated_at);