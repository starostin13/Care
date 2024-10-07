PRAGMA foreign_keys = 0;

CREATE TABLE sqlitestudio_temp_table AS SELECT *
                                          FROM mission_stack;

DROP TABLE mission_stack;

CREATE TABLE mission_stack (
    deploy              TEXT,
    rules               TEXT,
    cell                INTEGER,
    mission_description TEXT,
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    locked              INTEGER
);

INSERT INTO mission_stack (
                              deploy,
                              rules,
                              cell,
                              mission_description,
                              id
                          )
                          SELECT deploy,
                                 rules,
                                 cell,
                                 mission_description,
                                 id
                            FROM sqlitestudio_temp_table;

DROP TABLE sqlitestudio_temp_table;

PRAGMA foreign_keys = 1;
