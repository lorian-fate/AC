


import psycopg2
from .dbConnect import DbConnect





class UserManager:
    def __init__(self):
        self.db = DbConnect()
        self.db.connect()

    

    def add_user(self, username, email, password):
        hashed_password = password
        try:
            
            self.db.cursor.execute(
                """
                INSERT INTO usuarios (nombre_usuario, correo, contrasena)
                VALUES (%s, %s, %s)
                """,
                (username, email, password)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al añadir usuario: {e}")
            return False


    def get_users(self):
        try:
            query = "SELECT id, nombre_usuario, correo, creado_en, ultimo_login FROM usuarios;"
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
            self.db.cursor.close()

            usuarios = []
            for row in rows:
                usuarios.append({
                    "id": row[0],
                    "nombre_usuario": row[1],
                    "correo": row[2],
                    "creado_en": row[3],
                    "ultimo_login": row[4]
                })

            return usuarios

        except psycopg2.Error as e:
            return False, f"error: {str(e)}"

    def get_user_by_email(self, email):
        try:
            query = "SELECT id, nombre_usuario, correo, contrasena, creado_en, ultimo_login FROM usuarios WHERE correo = %s;"
            self.db.cursor.execute(query, (email,))
            row = self.db.cursor.fetchone()
            #self.db.cursor.close()

            if row:
                return {
                    "id": row[0],
                    "nombre_usuario": row[1],
                    "correo": row[2],
                    "contrasena": row[3],
                    "creado_en": row[4],
                    "ultimo_login": row[5]
                }
            return None

        except psycopg2.Error as e:
            print(f"Error al obtener usuario por correo: {e}")
            return None

"""
    user: 
        username: user001
        email: user001@example.com
        password: user001pass
    user2:
        username: user002
        email: user002@example.com
        password: user002pass
    user3:
        username: user003
        email: user003@example.com
        password: user003pass
"""
