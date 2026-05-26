from datetime import date, datetime
from calendar import monthrange

from flask import Blueprint, render_template, request
from flask_login import login_required

from models import Cliente, Servico, Venda


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


MESES_LABELS = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]


def converter_inteiro(valor, padrao):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def adicionar_meses(data_base, meses):
    mes_calculado = data_base.month - 1 + meses
    ano = data_base.year + mes_calculado // 12
    mes = mes_calculado % 12 + 1
    dia = min(data_base.day, monthrange(ano, mes)[1])

    return data_base.replace(year=ano, month=mes, day=dia)


def obter_periodicidade(venda):
    periodicidade = getattr(venda, "periodicidade", None) or "unica"

    if periodicidade not in ["unica", "mensal", "trimestral", "semestral", "anual"]:
        return "unica"

    return periodicidade


def intervalo_periodicidade_em_meses(periodicidade):
    intervalos = {
        "unica": None,
        "mensal": 1,
        "trimestral": 3,
        "semestral": 6,
        "anual": 12,
    }

    return intervalos.get(periodicidade)


def gerar_ocorrencias_receita(venda):
    if venda.tipo != "receita":
        return []

    inicio = getattr(venda, "data_inicio", None) or venda.data

    if not inicio:
        return []

    periodicidade = obter_periodicidade(venda)
    fim = getattr(venda, "data_fim", None)

    if periodicidade == "unica" or not fim:
        return [inicio]

    intervalo = intervalo_periodicidade_em_meses(periodicidade)

    if not intervalo:
        return [inicio]

    ocorrencias = []
    indice = 0

    while True:
        ocorrencia = adicionar_meses(inicio, intervalo * indice)

        if ocorrencia > fim:
            break

        ocorrencias.append(ocorrencia)
        indice += 1

        # Trava de segurança para evitar loop excessivo em datas muito longas.
        if indice > 240:
            break

    return ocorrencias


def anos_disponiveis(vendas):
    anos = {datetime.utcnow().date().year}

    for venda in vendas:
        if venda.data:
            anos.add(venda.data.year)

        if venda.tipo == "receita":
            for ocorrencia in gerar_ocorrencias_receita(venda):
                anos.add(ocorrencia.year)

    return sorted(anos, reverse=True)


def somar_dados_do_mes(vendas_validas, ano, mes):
    ultimo_dia = monthrange(ano, mes)[1]

    receitas_por_dia = [0 for _ in range(ultimo_dia)]
    custos_por_dia = [0 for _ in range(ultimo_dia)]

    for venda in vendas_validas:
        valor = venda.valor or 0

        if venda.tipo == "receita":
            for ocorrencia in gerar_ocorrencias_receita(venda):
                if ocorrencia.year == ano and ocorrencia.month == mes:
                    receitas_por_dia[ocorrencia.day - 1] += valor

        elif venda.tipo in ["custo", "despesa"]:
            if venda.data and venda.data.year == ano and venda.data.month == mes:
                custos_por_dia[venda.data.day - 1] += valor

    lucro_por_dia = [
        receitas_por_dia[i] - custos_por_dia[i]
        for i in range(ultimo_dia)
    ]

    return receitas_por_dia, custos_por_dia, lucro_por_dia


def somar_dados_do_ano(vendas_validas, ano):
    receitas_por_mes = [0 for _ in range(12)]
    custos_por_mes = [0 for _ in range(12)]

    for venda in vendas_validas:
        valor = venda.valor or 0

        if venda.tipo == "receita":
            for ocorrencia in gerar_ocorrencias_receita(venda):
                if ocorrencia.year == ano:
                    receitas_por_mes[ocorrencia.month - 1] += valor

        elif venda.tipo in ["custo", "despesa"]:
            if venda.data and venda.data.year == ano:
                custos_por_mes[venda.data.month - 1] += valor

    lucro_por_mes = [
        receitas_por_mes[i] - custos_por_mes[i]
        for i in range(12)
    ]

    return receitas_por_mes, custos_por_mes, lucro_por_mes


@dashboard_bp.route("/")
@login_required
def dashboard():
    hoje = datetime.utcnow().date()

    grafico_mes = request.args.get("grafico_mes", "").strip()
    grafico_ano = converter_inteiro(request.args.get("grafico_ano"), hoje.year)

    if grafico_mes:
        try:
            ano_diario, mes_diario = [int(parte) for parte in grafico_mes.split("-")]
        except ValueError:
            ano_diario = hoje.year
            mes_diario = hoje.month
    else:
        ano_diario = hoje.year
        mes_diario = hoje.month

    grafico_mes_valor = f"{ano_diario:04d}-{mes_diario:02d}"

    clientes_ativos = Cliente.query.filter_by(ativo=True).count()
    servicos_ativos = Servico.query.filter_by(ativo=True).count()

    vendas_validas = Venda.query.filter(
        Venda.status != "cancelado"
    ).all()

    todas_vendas = Venda.query.all()
    anos_para_select = anos_disponiveis(todas_vendas)

    if grafico_ano not in anos_para_select:
        anos_para_select.append(grafico_ano)
        anos_para_select = sorted(set(anos_para_select), reverse=True)

    receitas_por_dia, custos_por_dia, lucro_por_dia = somar_dados_do_mes(
        vendas_validas,
        ano_diario,
        mes_diario
    )

    receitas_por_mes, custos_por_mes, lucro_por_mes = somar_dados_do_ano(
        vendas_validas,
        grafico_ano
    )

    receitas_mes = sum(receitas_por_dia)
    custos_mes = sum(custos_por_dia)
    lucro_mes = receitas_mes - custos_mes

    total_receitas_ano = sum(receitas_por_mes)
    total_custos_ano = sum(custos_por_mes)
    lucro_ano = total_receitas_ano - total_custos_ano

    clientes_com_receita_ids = set()
    receitas_pendentes = 0
    total_receitas_validas = 0
    quantidade_receitas_validas = 0

    for venda in vendas_validas:
        if venda.tipo == "receita":
            ocorrencias = gerar_ocorrencias_receita(venda)
            total_da_venda = (venda.valor or 0) * len(ocorrencias)

            total_receitas_validas += total_da_venda
            quantidade_receitas_validas += len(ocorrencias)

            if venda.cliente_id:
                clientes_com_receita_ids.add(venda.cliente_id)

            if venda.status == "pendente":
                receitas_pendentes += total_da_venda

    ticket_medio = 0

    if quantidade_receitas_validas:
        ticket_medio = total_receitas_validas / quantidade_receitas_validas

    ultimos_lancamentos = Venda.query.order_by(
        Venda.data.desc(),
        Venda.id.desc()
    ).limit(8).all()

    dias_labels = [
        str(dia)
        for dia in range(1, monthrange(ano_diario, mes_diario)[1] + 1)
    ]

    return render_template(
        "dashboard.html",
        clientes_ativos=clientes_ativos,
        clientes_com_receita=len(clientes_com_receita_ids),
        servicos_ativos=servicos_ativos,
        receitas_mes=receitas_mes,
        custos_mes=custos_mes,
        lucro_mes=lucro_mes,
        receitas_pendentes=receitas_pendentes,
        ticket_medio=ticket_medio,
        total_receitas_ano=total_receitas_ano,
        total_custos_ano=total_custos_ano,
        lucro_ano=lucro_ano,
        dias_labels=dias_labels,
        receitas_por_dia=receitas_por_dia,
        custos_por_dia=custos_por_dia,
        lucro_por_dia=lucro_por_dia,
        meses_labels=MESES_LABELS,
        receitas_por_mes=receitas_por_mes,
        custos_por_mes=custos_por_mes,
        lucro_por_mes=lucro_por_mes,
        grafico_mes_valor=grafico_mes_valor,
        grafico_ano=grafico_ano,
        anos_para_select=anos_para_select,
        ultimos_lancamentos=ultimos_lancamentos
    )
