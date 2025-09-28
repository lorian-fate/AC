

import psycopg2
from .dbConnect import DbConnect




class FarmsManager:
    def __init__(self):
        self.db = DbConnect()
        self.db.connect()


    def add_farm(self, name, address, description, responsible):
        try:
            self.db.cursor.execute(
                """
                INSERT INTO fincas (name, address, description, responsible)
                VALUES (%s, %s, %s, %s)
                """,
                (name, address, description, responsible)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al añadir finca: {e}")
            return False


    def get_farms(self):
        try:
            self.db.cursor.execute("SELECT * FROM fincas")
            farms = self.db.cursor.fetchall()
            return farms
        except Exception as e:
            print(f"Error al obtener fincas: {e}")
            return []


    def update_farm(self, farm_id, name, address, description, responsible):
        try:
            self.db.cursor.execute(
                """
                UPDATE fincas
                SET name = %s, address = %s, description = %s, responsible = %s
                WHERE id = %s
                """,
                (name, address, description, responsible, farm_id)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al actualizar finca: {e}")
            return False

    def delete_farm(self, farm_id):
        try:
            self.db.cursor.execute(
                """
                DELETE FROM fincas
                WHERE id = %s
                """,
                (farm_id,)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error al eliminar finca: {e}")
            return False
        
    def get_by_id(self, farm_id):
        try:
            self.db.cursor.execute("SELECT * FROM fincas WHERE id = %s", (farm_id,))
            farm = self.db.cursor.fetchone()
            return farm
        except Exception as e:
            print(f"Error al obtener finca por ID: {e}")
            return None
