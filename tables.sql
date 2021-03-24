/*
To create the needed tables for the bot to function.
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/


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
    sort_date TIMESTAMP,
    jump_url VARCHAR
);

CREATE TABLE IF NOT EXISTS blacklist (
    user_id BIGINT,
    reason VARCHAR
)
