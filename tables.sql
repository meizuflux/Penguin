CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS prefixes (
    guild_id BIGINT REFERENCES guilds ON DELETE CASCADE,
    prefix VARCHAR NOT NULL,
    PRIMARY KEY (guild_id, prefix)
);

CREATE TABLE IF NOT EXISTS economy (
    user_id BIGINT PRIMARY KEY,
    wallet BIGINT,
    BANK BIGINT
);

CREATE TABLE IF NOT EXISTS stocks (
    user_id BIGINT,
    ticker VARCHAR,
    amount BIGINT,
    PRIMARY KEY (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS todos (
    user_id BIGINT,
    todo VARCHAR,
    sort_date DATE
)