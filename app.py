import os
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

from models import Usuario, db


def str_to_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def normalize_database_url(database_url):
    """Normaliza URLs PostgreSQL para o driver psycopg2 usado pelo SQLAlchemy."""
    if not database_url:
        return None

    database_url = database_url.strip()

    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgresql://"):]

    return database_url


def hide_database_password(database_url):
    """Retorna a URL sem expor a senha em mensagens de erro."""
    if not database_url:
        return "não configurada"

    parts = urlsplit(database_url)
    if "@" not in parts.netloc:
        return database_url

    credentials, host = parts.netloc.rsplit("@", 1)
    username = credentials.split(":", 1)[0]
    safe_netloc = f"{username}:***@{host}"
    return urlunsplit((parts.scheme, safe_netloc, parts.path, parts.query, parts.fragment))


def create_app():
    load_dotenv()

    app = Flask(
        __name__,
        static_folder="public",
        static_url_path="",
    )

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("A variável SECRET_KEY não foi configurada.")

    database_url = normalize_database_url(os.getenv("DATABASE_URL"))
    if not database_url:
        raise RuntimeError("A variável DATABASE_URL não foi configurada.")

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 2,
            "max_overflow": 0,
            "pool_timeout": 30,
        },
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=str_to_bool(
            os.getenv("SESSION_COOKIE_SECURE", "true" if os.getenv("VERCEL") else "false")
        ),
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=str_to_bool(
            os.getenv("SESSION_COOKIE_SECURE", "true" if os.getenv("VERCEL") else "false")
        ),
    )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar o sistema."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Usuario, int(user_id))
        except (TypeError, ValueError):
            return None

    from routes.auth import auth_bp
    from routes.clientes import clientes_bp
    from routes.dashboard import dashboard_bp
    from routes.kanban import kanban_bp
    from routes.servicos import servicos_bp
    from routes.vendas import vendas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(kanban_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(vendas_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    app.logger.info(
        "Banco configurado: %s",
        hide_database_password(database_url),
    )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=str_to_bool(os.getenv("FLASK_DEBUG", "false")),
    )
