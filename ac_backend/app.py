
import os
from flask import Flask, render_template, redirect, url_for, session
from dotenv import load_dotenv

# Cargar archivo .env automáticamente
load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "ac_frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "ac_frontend", "static")
)





# Clave secreta para sesiones
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

# Ruta de login
@app.route("/")
def home():
    # Si el usuario ya está logueado, redirigir al dashboard
    if session.get("user_email"):
        return redirect(url_for("dashboard"))
    return render_template("login/login.html")


# Dashboard (perfil del usuario)
@app.route("/dashboard")
def dashboard():
    if not session.get("user_email"):
        return redirect(url_for("home"))
    return render_template("index/dashboard.html", user_email=session["user_email"])


@app.route('/fincas')
def fincas_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('fincas/fincas.html')





@app.route("/register")
def register_page():
    return render_template("login/register.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))










