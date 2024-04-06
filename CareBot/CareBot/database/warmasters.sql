CREATE TABLE warmastrers (
    id          INTEGER PRIMARY KEY
                        NOT NULL
                        UNIQUE,
    telegram_id TEXT    UNIQUE
                        NOT NULL,
    alliance_id INTEGER
);
