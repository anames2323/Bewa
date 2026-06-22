import sqlite3 as sq

class DataBase:
    def __init__(self, db_file):
        self.connection = sq.connect(db_file)
        self.cur = self.connection.cursor()

    def db_start(self):
        with self.connection:
            self.cur.execute('CREATE TABLE IF NOT EXISTS users('
                             'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                             'user_id INTEGER,'
                             'username TEXT,'
                             'referi INTEGER,'
                             'username_referi TEXT,'
                             'UNIQUE(user_id))')

    def user_exists(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_user_referi(self, user_id, username, refere_id, username_referi):
        with self.connection:
            return self.cur.execute('INSERT INTO users (user_id, username, referi, username_referi) VALUES (?, ?, ?, ?)',
                                   (user_id, username, refere_id, username_referi))

    def add_user_no_referi(self, user_id, username, referi):
        with self.connection:
            return self.cur.execute('INSERT INTO users (user_id, username, referi) VALUES (?, ?, ?)', 
                                   (user_id, username, referi))

    def username_referi(self, user):
        with self.connection:
            result = self.cur.execute('SELECT username FROM users WHERE user_id = ?', (user,)).fetchall()
            if result:
                return result[0]
            return None