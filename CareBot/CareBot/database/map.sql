PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM map;

DROP TABLE map;

CREATE TABLE map (
    id            INTEGER PRIMARY KEY
                          UNIQUE
                          NOT NULL,
    planet_id     INTEGER,
    state         TEXT,
    patron        INTEGER,
    has_warehouse INTEGER DEFAULT (0) 
);

INSERT INTO map (
                    id,
                    planet_id,
                    state,
                    patron
                )
                SELECT id,
                       planet_id,
                       state,
                       patron
                  FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
