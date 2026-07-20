import os
from decimal import Decimal, InvalidOperation
from flask import Flask, redirect, url_for, jsonify
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from sqlalchemy import text
from models import db, Usuario


def normalizar_database_url(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def formatar_brl(valor):
    try:
        numero = Decimal(str(valor or 0))
    except (InvalidOperation, ValueError, TypeError):
        numero = Decimal("0")
    formatado = f"{numero:,.2f}"
    return "R$ " + formatado.replace(",", "X").replace(".", ",").replace("X", ".")


def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder="public", static_url_path="")
    database_url = normalizar_database_url(os.getenv("DATABASE_URL"))
    if not database_url:
        database_url = "sqlite:///hubstudio_novo.db"

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    )
    db.init_app(app)
    app.jinja_env.filters["brl"] = formatar_brl

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar o sistema."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.produtos import produtos_bp
    from routes.prospeccoes import prospeccoes_bp
    from routes.propostas import propostas_bp
    from routes.clientes import clientes_bp
    from routes.producao import producao_bp

    for blueprint in [auth_bp, dashboard_bp, produtos_bp, prospeccoes_bp, propostas_bp, clientes_bp, producao_bp]:
        app.register_blueprint(blueprint)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.dashboard") if current_user.is_authenticated else url_for("auth.login"))

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify(status="ok")
        except Exception:
            return jsonify(status="error"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
