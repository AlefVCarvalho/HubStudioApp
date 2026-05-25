import os

from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from dotenv import load_dotenv

from models import db, Usuario


def str_to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]


def create_app():
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave-padrao-dev")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(app.instance_path, 'hubstudio.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar o sistema."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.clientes import clientes_bp
    from routes.servicos import servicos_bp
    from routes.vendas import vendas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(servicos_bp)
    app.register_blueprint(vendas_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()

        admin_email = os.getenv("ADMIN_EMAIL", "admin@hubstudio.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        admin_nome = os.getenv("ADMIN_NOME", "Administrador")

        usuario_admin = Usuario.query.filter_by(usuario=admin_email).first()

        if not usuario_admin:
            usuario_admin = Usuario(
                usuario=admin_email,
                nome=admin_nome
            )
            usuario_admin.definir_senha(admin_password)

            db.session.add(usuario_admin)
            db.session.commit()

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = str_to_bool(os.getenv("FLASK_DEBUG", "False"))

    app.run(
        host=host,
        port=port,
        debug=debug
    )