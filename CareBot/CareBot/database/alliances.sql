PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM alliances;

DROP TABLE alliances;

CREATE TABLE alliances (
    name            TEXT    NOT NULL
                            UNIQUE,
    id              INTEGER UNIQUE
                            NOT NULL
                            PRIMARY KEY,
    common_resource INTEGER DEFAULT (0) 
);

INSERT INTO alliances (
                          name,
                          id
                      )
                      SELECT name,
                             id
                        FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
