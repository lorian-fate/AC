from flask import Blueprint, request, jsonify
from flask import session

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
def login():
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return jsonify({"success": False, "message": "Faltan credenciales"}), 400

    email = data["email"].strip()
    password = data["password"].strip()

    usuario = next((u for u in USERS if u["email"] == email), None)
    if usuario and usuario["password"] == password:
        session["user_email"] = usuario["email"]
        session["user_name"] = usuario["nombre"]
        return jsonify({"success": True, "message": f"Bienvenido, {usuario['nombre']}!"}), 200
    else:
        return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401
