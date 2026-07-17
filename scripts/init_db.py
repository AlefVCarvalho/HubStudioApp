import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from models import Usuario, db


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"A variável {name} não foi configurada.")
    return value


with app.app_context():
    db.create_all()

    admin_email = required_env("ADMIN_EMAIL")
    admin_password = required_env("ADMIN_PASSWORD")
    admin_nome = os.getenv("ADMIN_NOME", "Administrador").strip() or "Administrador"

    usuario_admin = Usuario.query.filter_by(usuario=admin_email).first()

    if usuario_admin is None:
        usuario_admin = Usuario(usuario=admin_email, nome=admin_nome)
        usuario_admin.definir_senha(admin_password)
        db.session.add(usuario_admin)
        action = "criado"
    else:
        usuario_admin.nome = admin_nome
        usuario_admin.definir_senha(admin_password)
        action = "atualizado"

    db.session.commit()
    print(f"Banco inicializado e administrador {action}: {admin_email}")
