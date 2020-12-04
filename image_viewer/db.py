import sqlite3

def dict_factory(cursor, row): 
    d = {} 
    for idx, col in enumerate(cursor.description): 
        d[col[0]] = row[idx] 
    return d

class Db(object):
    def __init__(self, database, logger):
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = dict_factory
        self.connection.execute('PRAGMA FOREIGN_KEYS=ON')
        self.logger = logger

    def close(self):
        self.connection.close()

    def insert_task(self, directory_key, task_type):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                INSERT INTO task
                (directory_key, type)
                VALUES (?, ?)""", (directory_key, task_type))
                self.logger.info('Insert task success.')
                connection.commit()
                return cursor.lastrowid
            except Exception as e:
                self.logger.error(e)
                connection.rollback()
                return 0
            finally:
                cursor.close()

    def insert_images(self, task_id, image_keys, annotations=None):
        if annotations is None:
            annotations = map(lambda _: None, image_keys)
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.executemany("""
                INSERT INTO image
                (task_id, image_key, annotation)
                VALUES (?, ?, ?)""",
                [(task_id, image_key, annotation) for (image_key, annotation) in zip(image_keys, annotations)])
                connection.commit()
                self.logger.info('Insert images success.')
                return cursor.rowcount
            except Exception as e:
                self.logger.error(e)
                connection.rollback()
                return 0
            finally:
                cursor.close()

    def select_tasks(self):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                SELECT id task_id, directory_key, create_time
                FROM task
                ORDER BY task_id DESC""")
                self.logger.info('Select tasks success.')
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(e)
                return []
            finally:
                cursor.close()

    def select_tasks_with_id(self, task_id):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                SELECT id task_id, directory_key, type, create_time
                FROM task
                WHERE id = ?""", (task_id,))
                self.logger.info('Select tasks success.')
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(e)
                return []
            finally:
                cursor.close()

    def delete_tasks_with_id(self, task_id):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                DELETE FROM image
                WHERE task_id = ?""", (task_id,))
                cursor.execute("""
                DELETE FROM task
                WHERE id = ?""", (task_id,))
                self.logger.info('Delete tasks success.')
                return cursor.rowcount
            except Exception as e:
                self.logger.error(e)
                return None
            finally:
                cursor.close()

    def select_images_with_task(self, task_id, limit=None, offset=0):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cmd = """
                SELECT id image_id, image_key, selected
                FROM image
                WHERE task_id = ?
                ORDER BY image_id ASC
                """
                args = [task_id,]
                if limit:
                    cmd += 'LIMIT ? '
                    args.append(limit)
                    if offset:
                        cmd += 'OFFSET ? '
                        args.append(offset)
                cursor.execute(cmd, args)
                self.logger.info('Select images success.')
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(e)
                return []
            finally:
                cursor.close()

    def select_selected_images_with_task(self, task_id):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                SELECT image_key
                FROM image
                WHERE selected = 1
                AND task_id = ?
                ORDER BY id ASC""", (task_id,))
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(e)
                return []
            finally:
                cursor.close()

    def select_images_with_id(self, image_id):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                SELECT id image_id, image_key, selected, task_id, annotation
                FROM image
                WHERE image_id = ?""", (image_id,))
                self.logger.info('Select images success.')
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(e)
                return []
            finally:
                cursor.close()

    def update_image_selection(self, image_id, selected):
        with self.connection as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                UPDATE image
                SET selected = ?
                WHERE id = ?""", (selected, image_id))
                self.logger.info('Update image success.')
                connection.commit()
                return cursor.rowcount
            except Exception as e:
                self.logger.error(e)
                return 0
            finally:
                cursor.close()
