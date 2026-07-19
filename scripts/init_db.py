import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from models import db, Usuario

with app.app_context():
    db.create_all()
    email = os.getenv("ADMIN_EMAIL")
    senha = os.getenv("ADMIN_PASSWORD")
    nome = os.getenv("ADMIN_NOME", "Administrador")
    if email and senha:
        usuario = Usuario.query.filter_by(usuario=email).first()
        if not usuario:
            usuario = Usuario(usuario=email, nome=nome)
            db.session.add(usuario)
        usuario.nome = nome
        usuario.definir_senha(senha)
        db.session.commit()
    print("Banco preparado com sucesso.")
