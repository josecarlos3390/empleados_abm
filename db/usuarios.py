from db.connection import db
from datetime import datetime

def get_all_users():
    return db.fetch_all("SELECT * FROM usuarios ORDER BY id DESC")

def get_user_by_id(uid):
    return db.fetch_one("SELECT * FROM usuarios WHERE id = %s", (uid,))

def get_user_by_username(username):
    return db.fetch_one("SELECT * FROM usuarios WHERE username = %s", (username,))

def create_user(nombre, username, password_hash, rol):
    return db.execute_query("INSERT INTO usuarios (nombre, username, password, rol) VALUES (%s,%s,%s,%s)",
                            (nombre, username, password_hash, rol))

def update_user(uid, nombre, username, rol):
    return db.execute_query("UPDATE usuarios SET nombre=%s, username=%s, rol=%s WHERE id=%s",
                            (nombre, username, rol, uid))

def delete_user(uid):
    return db.execute_query("DELETE FROM usuarios WHERE id=%s", (uid,))
