from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from models import Cliente, Servico, Venda


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def dashboard():
    hoje = datetime.utcnow().date()
    ano_atual = hoje.year
    mes_atual = hoje.month

    clientes_ativos = Cliente.query.filter_by(ativo=True).count()
    servicos_ativos = Servico.query.filter_by(ativo=True).count()

    vendas_validas = Venda.query.filter(
        Venda.status != "cancelado"
    ).all()

    receitas_mes = 0
    despesas_mes = 0

    receitas_por_mes = [0 for _ in range(12)]
    despesas_por_mes = [0 for _ in range(12)]

    for venda in vendas_validas:
        if not venda.data:
            continue

        if venda.data.year != ano_atual:
            continue

        indice_mes = venda.data.month - 1

        if venda.tipo == "receita":
            receitas_por_mes[indice_mes] += venda.valor or 0

            if venda.data.month == mes_atual:
                receitas_mes += venda.valor or 0

        elif venda.tipo == "despesa":
            despesas_por_mes[indice_mes] += venda.valor or 0

            if venda.data.month == mes_atual:
                despesas_mes += venda.valor or 0

    lucro_mes = receitas_mes - despesas_mes

    lucro_por_mes = [
        receitas_por_mes[i] - despesas_por_mes[i]
        for i in range(12)
    ]

    ultimos_lancamentos = Venda.query.order_by(
        Venda.data.desc(),
        Venda.id.desc()
    ).limit(8).all()

    total_receitas_ano = sum(receitas_por_mes)
    total_despesas_ano = sum(despesas_por_mes)
    lucro_ano = total_receitas_ano - total_despesas_ano

    meses_labels = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    return render_template(
        "dashboard.html",
        ano_atual=ano_atual,
        clientes_ativos=clientes_ativos,
        servicos_ativos=servicos_ativos,
        receitas_mes=receitas_mes,
        despesas_mes=despesas_mes,
        lucro_mes=lucro_mes,
        total_receitas_ano=total_receitas_ano,
        total_despesas_ano=total_despesas_ano,
        lucro_ano=lucro_ano,
        meses_labels=meses_labels,
        receitas_por_mes=receitas_por_mes,
        despesas_por_mes=despesas_por_mes,
        lucro_por_mes=lucro_por_mes,
        ultimos_lancamentos=ultimos_lancamentos
    )