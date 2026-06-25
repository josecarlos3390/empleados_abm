from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash('Debes iniciar sesión primero.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if not user or user.get('rol') != 'admin':
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('empleados.lista_empleados'))
        return f(*args, **kwargs)
    return wrapper
