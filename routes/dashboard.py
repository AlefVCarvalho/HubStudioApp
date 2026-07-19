from collections import Counter
from flask import Blueprint, render_template
from flask_login import login_required
from models import Produto, Contato, Producao

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@login_required
def dashboard():
    produtos = Produto.query.count()
    prospeccoes = Contato.query.filter_by(fase="prospeccao").count()
    propostas = Contato.query.filter_by(fase="proposta").count()
    clientes = Contato.query.filter_by(fase="cliente").count()
    producoes = Producao.query.all()
    etapas_ordem = ["alinhamento", "materiais", "producao", "ajustes", "entrega"]
    contagem = Counter(item.etapa for item in producoes)
    mensal = sum(float(item.valor_mensal) for item in producoes)
    pontual = sum(float(item.valor_pontual) for item in producoes)
    return render_template("dashboard.html", produtos=produtos, prospeccoes=prospeccoes, propostas=propostas, clientes=clientes, producoes=len(producoes), receita_mensal=mensal, receita_pontual=pontual, grafico_labels=[e.title() for e in etapas_ordem], grafico_valores=[contagem[e] for e in etapas_ordem])
