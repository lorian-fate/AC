from flask import Blueprint, request, jsonify
from flask import session
import re
from werkzeug.security import generate_password_hash, check_password_hash
from ac_backend.db_manager.userManager import UserManager

user_manager = UserManager()


api_bp = Blueprint("api", __name__)

# Usuario de ejemplo (para demo)
USERS = [
    {
        "email": "usuario@correo.com",
        "password": "123456",  # En producción, nunca almacenar contraseñas en texto plano
        "nombre": "Juan Pérez"
    }
]

# Endpoint de login
@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.json
    correo = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not correo or not password:
        return jsonify({'success': False, 'message': 'Faltan credenciales'}), 400

    user = user_manager.get_user_by_email(correo)
    print("======================================================")
    print(f"iniciando checkout para usuario: {user}")
    print("======================================================")
    if user and check_password_hash(user["contrasena"], password):
        print("Usuario autenticado correctamente")
        session['user_id'] = user["id"]
        session['user_name'] = user["nombre_usuario"]
        session['user_email'] = user["correo"]
        return jsonify({'success': True, 'message': f'Bienvenido, {user["nombre_usuario"]}!'}), 200
    else:
        return jsonify({'success': False, 'message': 'Correo o contraseña incorrectos'}), 401
    





@api_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    usuario = data.get("usuario", "").strip()
    correo = data.get("correo", "").strip()
    password = data.get("password", "").strip()

    if not usuario or not correo or not password:
        return jsonify({"success": False, "message": "Todos los campos son obligatorios"}), 400

    # Validación básica correo
    if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
        return jsonify({"success": False, "message": "Correo inválido"}), 400

    # Validación contraseña mínima 6 caracteres
    if len(password) < 6:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 6 caracteres"}), 400

    # Verificar si usuario o correo ya existen (simulación)
    #for u in USERS:
    #    if u["usuario"] == usuario or u["correo"] == correo:
    #        return jsonify({"success": False, "message": "Usuario o correo ya registrado"}), 409

    # Hashear contraseña
    hashed_password = generate_password_hash(password)

    # Guardar usuario nuevo (simulado)
    user_manager.add_user(usuario, correo, hashed_password)


    return jsonify({"success": True, "message": "Registro exitoso"}), 201