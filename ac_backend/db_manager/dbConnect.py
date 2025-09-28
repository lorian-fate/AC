import psycopg2
from werkzeug.security import generate_password_hash





class DbConnect:    
    DB_CONFIG = {
        "dbname": "AC-DDBB",
        "user": "postgres",
        "password": "destiny",
        "host": "localhost",
        "port": "5432"
    }

    def __init__(self):
        # Limpiar posibles caracteres extraños en los valores de configuración
        for k, v in self.DB_CONFIG.items():
            if isinstance(v, str):
                self.DB_CONFIG[k] = v.strip()
        self.connect()

    def connect(self):
        self.connection = psycopg2.connect(**self.DB_CONFIG)
        self.cursor = self.connection.cursor()
        return self.connection, self.cursor
    

    def disconnect(self):
        self.cursor.close()
        self.connection.close()


