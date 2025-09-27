from ac_backend.app import app
from ac_backend.routes.api import api_bp



# Registrar Blueprint
app.register_blueprint(api_bp, url_prefix="/api")


if __name__ == "__main__":
    app.run(debug=True)
