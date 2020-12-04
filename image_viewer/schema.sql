DROP TABLE IF EXISTS task;
CREATE TABLE task
(
	id				INTEGER PRIMARY KEY AUTOINCREMENT,
	directory_key	CHAR(200),
    type            CHAR(200),
    create_time     DATETIME DEFAULT (datetime('now', 'localtime'))
);

DROP TABLE IF EXISTS image;
CREATE TABLE image
(
	id				INTEGER PRIMARY KEY AUTOINCREMENT,
	task_id         INTEGER,
	image_key		CHAR(200),
	selected		INTEGER DEFAULT 0,
    annotation      TEXT,
	FOREIGN KEY (task_id) REFERENCES task(id)
);
