PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM map;

DROP TABLE map;

CREATE TABLE map (
    id        INTEGER PRIMARY KEY,
    planet_id INTEGER,
    state     TEXT,
    patron    INTEGER
);

INSERT INTO map (
                    id,
                    planet_id,
                    state
                )
                SELECT id,
                       planet_id,
                       state
                  FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
