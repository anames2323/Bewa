import sqlite3 as sq

class DataBase:
    def __init__(self, db_file):
        self.connection = sq.connect(db_file)
        self.cur = self.connection.cursor()

    def db_start(self):
        with self.connection:
            # Таблица пользователей
            self.cur.execute('CREATE TABLE IF NOT EXISTS users('
                             'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                             'user_id INTEGER,'
                             'username TEXT,'
                             'referi INTEGER,'
                             'username_referi TEXT,'
                             'UNIQUE(user_id))')
            
            # Таблица администраторов
            self.cur.execute('CREATE TABLE IF NOT EXISTS admins('
                             'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                             'user_id INTEGER UNIQUE,'
                             'username TEXT,'
                             'added_by INTEGER)')
            
            # Таблица каналов
            self.cur.execute('CREATE TABLE IF NOT EXISTS channels('
                             'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                             'channel_id INTEGER UNIQUE,'
                             'channel_url TEXT,'
                             'channel_name TEXT,'
                             'added_by INTEGER,'
                             'is_active INTEGER DEFAULT 1)')

    # ---------- ПОЛЬЗОВАТЕЛИ ----------
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

    # ---------- АДМИНИСТРАТОРЫ ----------
    def is_admin(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_admin(self, user_id, username, added_by):
        with self.connection:
            try:
                self.cur.execute('INSERT INTO admins (user_id, username, added_by) VALUES (?, ?, ?)',
                               (user_id, username, added_by))
                return True
            except:
                return False

    def remove_admin(self, user_id):
        with self.connection:
            self.cur.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
            return True

    def get_all_admins(self):
        with self.connection:
            return self.cur.execute('SELECT user_id, username FROM admins').fetchall()

    # ---------- КАНАЛЫ ----------
    def add_channel(self, channel_id, channel_url, channel_name, added_by):
        with self.connection:
            try:
                self.cur.execute('INSERT INTO channels (channel_id, channel_url, channel_name, added_by) VALUES (?, ?, ?, ?)',
                               (channel_id, channel_url, channel_name, added_by))
                return True
            except:
                return False

    def remove_channel(self, channel_id):
        with self.connection:
            self.cur.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
            return True

    def toggle_channel(self, channel_id, is_active):
        with self.connection:
            self.cur.execute('UPDATE channels SET is_active = ? WHERE channel_id = ?', (is_active, channel_id))
            return True

    def get_all_channels(self):
        with self.connection:
            return self.cur.execute('SELECT channel_id, channel_url, channel_name, is_active FROM channels').fetchall()

    def get_active_channels(self):
        with self.connection:
            return self.cur.execute('SELECT channel_id, channel_url, channel_name FROM channels WHERE is_active = 1').fetchall()

    def channel_exists(self, channel_id):
        with self.connection:
            result = self.cur.execute('SELECT * FROM channels WHERE channel_id = ?', (channel_id,)).fetchall()
            return bool(len(result))
