from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.security import admin_required, login_required
from db.usuarios import get_all_users, get_user_by_id, create_user, update_user, delete_user
from werkzeug.security import generate_password_hash
from datetime import datetime

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


# 🧾 LISTAR USUARIOS
@usuarios_bp.route('/', endpoint='lista_usuarios')
@admin_required
def lista_usuarios():
    usuarios = get_all_users()
    return render_template('usuarios/list.html', usuarios=usuarios)


# ➕ AGREGAR USUARIO
@usuarios_bp.route('/add', methods=['GET', 'POST'], endpoint='agregar_usuario')
@admin_required
def agregar_usuario():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        rol = request.form.get('rol')

        if not username or not password or not rol:
            flash('Por favor completa todos los campos obligatorios.', 'warning')
            return redirect(url_for('usuarios.agregar_usuario'))

        hashed = generate_password_hash(password)
        create_user(nombre, username, hashed, rol)
        flash('✅ Usuario creado correctamente.', 'success')
        return redirect(url_for('usuarios.lista_usuarios'))

    return render_template('usuarios/add.html')


# ✏️ EDITAR USUARIO
@usuarios_bp.route('/edit/<int:id>', methods=['GET', 'POST'], endpoint='editar_usuario')
@admin_required
def editar_usuario(id):
    usuario = get_user_by_id(id)
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('usuarios.lista_usuarios'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        username = request.form.get('username', '').strip()
        rol = request.form.get('rol')

        update_user(id, nombre, username, rol)
        flash('✅ Usuario actualizado correctamente.', 'success')
        return redirect(url_for('usuarios.lista_usuarios'))

    return render_template('usuarios/edit.html', usuario=usuario)


# ❌ ELIMINAR USUARIO
@usuarios_bp.route('/delete/<int:id>', endpoint='eliminar_usuario')
@admin_required
def eliminar_usuario(id):
    delete_user(id)
    flash('🗑️ Usuario eliminado correctamente.', 'info')
    return redirect(url_for('usuarios.lista_usuarios'))
