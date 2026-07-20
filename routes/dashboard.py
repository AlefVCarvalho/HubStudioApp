from collections import Counter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template
from flask_login import login_required
from models import Produto, Contato, Producao


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


@dashboard_bp.route("/")
@login_required
def dashboard():
    produtos = Produto.query.count()
    prospeccoes = Contato.query.filter_by(fase="prospeccao").count()
    propostas = Contato.query.filter_by(fase="proposta").count()
    clientes = Contato.query.filter_by(fase="cliente").count()

    todas_producoes = Producao.query.all()
    producoes_ativas = [item for item in todas_producoes if item.etapa != "entrega"]

    etapas_ordem = ["alinhamento", "materiais", "producao", "ajustes"]
    nomes_etapas = {
        "alinhamento": "Alinhamento",
        "materiais": "Materiais",
        "producao": "Produção",
        "ajustes": "Ajustes",
    }
    contagem_producao = Counter(item.etapa for item in producoes_ativas)

    receita_mensal = sum(float(item.valor or 0) for item in todas_producoes if item.periodicidade == "mensal")
    receita_pontual = sum(float(item.valor or 0) for item in producoes_ativas if item.periodicidade == "pontual")

    hoje = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    meses = [hoje - relativedelta(months=i) for i in range(11, -1, -1)]
    receitas_mensais = []
    receitas_pontuais = []

    for mes in meses:
        inicio = mes
        fim = mes + relativedelta(months=1)
        total_mensal = 0.0
        total_pontual = 0.0

        for item in todas_producoes:
            criado_em = item.criado_em or hoje
            valor = float(item.valor or 0)
            if item.periodicidade == "mensal" and criado_em < fim:
                total_mensal += valor
            elif item.periodicidade == "pontual" and inicio <= criado_em < fim:
                total_pontual += valor

        receitas_mensais.append(total_mensal)
        receitas_pontuais.append(total_pontual)

    return render_template(
        "dashboard.html",
        produtos=produtos,
        prospeccoes=prospeccoes,
        propostas=propostas,
        clientes=clientes,
        producoes=len(producoes_ativas),
        receita_mensal=receita_mensal,
        receita_pontual=receita_pontual,
        grafico_producao_labels=[nomes_etapas[e] for e in etapas_ordem],
        grafico_producao_valores=[contagem_producao[e] for e in etapas_ordem],
        grafico_clientes_labels=["Prospecções", "Propostas", "Clientes"],
        grafico_clientes_valores=[prospeccoes, propostas, clientes],
        grafico_receitas_labels=[f"{MESES_PT[m.month - 1]}/{str(m.year)[2:]}" for m in meses],
        grafico_receitas_mensais=receitas_mensais,
        grafico_receitas_pontuais=receitas_pontuais,
    )
