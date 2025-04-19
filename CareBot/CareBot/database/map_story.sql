PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM map_story;

DROP TABLE map_story;

CREATE TABLE map_story (
    hex_id  INTEGER,
    content TEXT,
    UNIQUE (
        hex_id,
        content
    )
);

INSERT INTO map_story (
                          hex_id,
                          content
                      )
                      SELECT hex_id,
                             content
                        FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
