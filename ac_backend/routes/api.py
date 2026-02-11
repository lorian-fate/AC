from flask import Blueprint, request, jsonify
from flask import session
import re


from werkzeug.security import generate_password_hash, check_password_hash
from ac_backend.db_manager.userManager import UserManager
from ac_backend.db_manager.farmsManager import FarmsManager




user_manager = UserManager()
farms_manager = FarmsManager()



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





@api_bp.route('/farms', methods=['GET'])
def get_farms():
    allFarms = farms_manager.get_farms()
    farms = []
    for farm in allFarms:
        farms.append({
            "id": farm[0],
            "nombre": farm[1],
            "direccion": farm[2],
            "descripcion": farm[3]
        })
    return jsonify(farms)




@api_bp.route('/fincas', methods=['POST'])
def create_finca():
    data = request.json
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({"success": False, "message": "El nombre es obligatorio"}), 400
    
    farms_manager.add_farm(
        name=nombre,
        address=data.get('direccion', '').strip(),
        description=data.get('descripcion', '').strip(),
        responsible=data.get('responsable', '').strip()
    )
    """
    finca = Finca(nombre=nombre,
                  direccion=data.get('direccion', '').strip(),
                  descripcion=data.get('descripcion', '').strip(),
                  responsable=session.get('user_id')
                  )

    db.session.add(finca)
    db.session.commit()"""

    #return jsonify({"success": True, "finca": finca.to_dict()}), 201
    return jsonify({"success": True, "message": "Finca creada"}), 201




@api_bp.route('/fincas/<int:id>', methods=['PUT'])
def update_finca(id):

    finca = farms_manager.get_farm_by_id(id)
    if not finca:
        return jsonify({"success": False, "message": "Finca no encontrada"}), 404
    
    data = request.json
    nombre = data.get('nombre', '').strip()
    if not nombre:
        return jsonify({"success": False, "message": "El nombre es obligatorio"}), 400
    
    farms_manager.update_farm(
        farm_id=id,
        name=nombre,
        address=data.get('direccion', '').strip(),
        description=data.get('descripcion', '').strip(),
        responsible=data.get('responsable', '').strip()
    )

    return jsonify({"success": True, "message": "Finca actualizada"}), 200





@api_bp.route('/fincas/<int:id>', methods=['DELETE'])
def delete_finca(id):
    finca = farms_manager.get_farm_by_id(id)
    if not finca:
        return jsonify({"success": False, "message": "Finca no encontrada"}), 404

    farms_manager.delete_farm(id)
    return jsonify({"success": True, "message": "Finca eliminada"})













# Simulación de base de datos para los datos de formularios
# En producción usarías una tabla SQL: id, user_id, task_name, form_data (JSON)
TASK_STORAGE = {}

@api_bp.route('/api/task-data/<string:task_name>', methods=['GET'])
def get_task_data(task_name):
    # Retorna los datos guardados para esa tarea
    data = TASK_STORAGE.get(task_name, {})
    return jsonify({"success": True, "data": data})

@api_bp.route('/api/task-data/<string:task_name>', methods=['POST'])
def save_task_data(task_name):
    data = request.json
    TASK_STORAGE[task_name] = data  # Guardamos los datos
    return jsonify({"success": True, "message": "Datos guardados correctamente"})

@api_bp.route('/api/execute-task', methods=['POST'])
def execute_task_backend():
    data = request.json
    task_name = data.get('task_name')
    form_data = data.get('form_data') # Aquí llegan los datos del formulario
    
    print(f"--- EJECUTANDO TAREA EN BACKEND: {task_name} ---")
    print(f"Datos procesados: {form_data}")
    
    return jsonify({"success": True, "message": f"Tarea {task_name} ejecutada con éxito"})