import os
import sys
from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app
from models import db, Usuario, Producao, ProducaoChecklist


def adicionar_coluna_se_faltar(tabela, coluna, definicao):
    insp = inspect(db.engine)
    if tabela not in insp.get_table_names():
        return
    colunas = {item["name"] for item in insp.get_columns(tabela)}
    if coluna not in colunas:
        db.session.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"))
        db.session.commit()


with app.app_context():
    db.create_all()

    adicionar_coluna_se_faltar("producoes", "criado_em", "TIMESTAMP")
    adicionar_coluna_se_faltar("producoes", "concluido_em", "TIMESTAMP")
    db.session.execute(text("UPDATE producoes SET criado_em = CURRENT_TIMESTAMP WHERE criado_em IS NULL"))
    db.session.commit()

    # Cria checklists para produções antigas usando o primeiro produto vinculado.
    for producao in Producao.query.all():
        if producao.checklist or not producao.produto_item or not producao.produto_item.produto:
            continue
        for etapa in producao.produto_item.produto.etapas:
            producao.checklist.append(
                ProducaoChecklist(
                    produto_etapa_id=etapa.id,
                    descricao=etapa.descricao,
                    ordem=etapa.ordem,
                    concluida=False,
                )
            )
    db.session.commit()

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
