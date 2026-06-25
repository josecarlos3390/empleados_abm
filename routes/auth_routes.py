from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db.usuarios import get_user_by_username

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        if user and check_password_hash(user['password'], password):
            session['user'] = {'id': user['id'], 'username': user['username'], 'rol': user['rol']}
            flash('Bienvenido', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', body_class='login-page')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('auth.login'))
