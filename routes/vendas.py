from datetime import datetime
from calendar import monthrange

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Venda, Cliente, Servico


vendas_bp = Blueprint("vendas", __name__, url_prefix="/vendas")


PERIODICIDADES_RECEITA = {
    "unica": "Única",
    "mensal": "Mensal",
    "trimestral": "Trimestral",
    "semestral": "Semestral",
    "anual": "Anual",
}


def converter_data(data_texto):
    if not data_texto:
        return None

    try:
        return datetime.strptime(data_texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def converter_inteiro(valor):
    try:
        return int(valor) if valor else None
    except ValueError:
        return None


def adicionar_meses(data_base, meses):
    mes_calculado = data_base.month - 1 + meses
    ano = data_base.year + mes_calculado // 12
    mes = mes_calculado % 12 + 1
    dia = min(data_base.day, monthrange(ano, mes)[1])

    return data_base.replace(year=ano, month=mes, day=dia)


def obter_periodicidade(venda):
    periodicidade = getattr(venda, "periodicidade", None) or "unica"

    if periodicidade not in PERIODICIDADES_RECEITA:
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

        if indice > 240:
            break

    return ocorrencias


def totalizar_receita_periodica(venda):
    if venda.status == "cancelado":
        return 0

    return (venda.valor or 0) * len(gerar_ocorrencias_receita(venda))


@vendas_bp.route("/")
@login_required
def vendas():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "").strip()
    cliente_id = converter_inteiro(request.args.get("cliente_id", "").strip())
    servico_id = converter_inteiro(request.args.get("servico_id", "").strip())

    query = Venda.query

    if busca:
        query = query.filter(
            Venda.descricao.ilike(f"%{busca}%") |
            Venda.forma_pagamento.ilike(f"%{busca}%") |
            Venda.observacoes.ilike(f"%{busca}%")
        )

    if status:
        query = query.filter(Venda.status == status)

    if cliente_id:
        query = query.filter(Venda.cliente_id == cliente_id)

    if servico_id:
        query = query.filter(Venda.servico_id == servico_id)

    receitas = (
        query
        .filter(Venda.tipo == "receita")
        .order_by(Venda.data.desc(), Venda.id.desc())
        .all()
    )

    custos = (
        query
        .filter(Venda.tipo.in_(["custo", "despesa"]))
        .order_by(Venda.data.desc(), Venda.id.desc())
        .all()
    )

    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome.asc()).all()
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome.asc()).all()

    total_receitas = sum(totalizar_receita_periodica(venda) for venda in receitas)
    total_custos = sum(venda.valor for venda in custos if venda.status != "cancelado")
    saldo = total_receitas - total_custos

    ocorrencias_por_venda = {
        venda.id: gerar_ocorrencias_receita(venda)
        for venda in receitas
    }

    return render_template(
        "vendas.html",
        receitas=receitas,
        custos=custos,
        clientes=clientes,
        servicos=servicos,
        busca=busca,
        status=status,
        cliente_id=cliente_id or "",
        servico_id=servico_id or "",
        total_receitas=total_receitas,
        total_custos=total_custos,
        saldo=saldo,
        periodicidades_receita=PERIODICIDADES_RECEITA,
        ocorrencias_por_venda=ocorrencias_por_venda
    )


@vendas_bp.route("/novo", methods=["POST"])
@login_required
def novo_lancamento():
    tipo = request.form.get("tipo", "").strip()

    if tipo == "despesa":
        tipo = "custo"

    descricao = request.form.get("descricao", "").strip()
    cliente_id = converter_inteiro(request.form.get("cliente_id", "").strip())
    servico_id = converter_inteiro(request.form.get("servico_id", "").strip())
    valor = request.form.get("valor", "0").strip().replace(",", ".")
    data = request.form.get("data", "").strip()
    data_inicio = request.form.get("data_inicio", "").strip()
    data_fim = request.form.get("data_fim", "").strip()
    periodicidade = request.form.get("periodicidade", "unica").strip()
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    status = request.form.get("status", "pago").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if tipo not in ["receita", "custo"]:
        flash("Escolha uma aba válida para lançar receita ou custo.", "warning")
        return redirect(url_for("vendas.vendas"))

    if not descricao:
        flash("A descrição do lançamento é obrigatória.", "warning")
        return redirect(url_for("vendas.vendas"))

    try:
        valor = float(valor)
    except ValueError:
        flash("Informe um valor válido.", "warning")
        return redirect(url_for("vendas.vendas"))

    if valor <= 0:
        flash("O valor precisa ser maior que zero.", "warning")
        return redirect(url_for("vendas.vendas"))

    data_convertida = converter_data(data)
    data_inicio_convertida = converter_data(data_inicio)
    data_fim_convertida = converter_data(data_fim)

    if tipo == "receita":
        if not cliente_id:
            flash("Selecione um cliente para cadastrar a receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if not servico_id:
            flash("Selecione um serviço para cadastrar a receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if not data_inicio_convertida:
            flash("Informe a data de início do período da receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if periodicidade not in PERIODICIDADES_RECEITA:
            periodicidade = "unica"

        if periodicidade != "unica" and not data_fim_convertida:
            flash("Informe a data de fim para receitas periódicas.", "warning")
            return redirect(url_for("vendas.vendas"))

        if data_fim_convertida and data_fim_convertida < data_inicio_convertida:
            flash("A data de fim não pode ser anterior à data de início.", "warning")
            return redirect(url_for("vendas.vendas"))

        data_convertida = data_inicio_convertida

    if tipo == "custo":
        if not data_convertida:
            flash("Informe a data do custo.", "warning")
            return redirect(url_for("vendas.vendas"))

        cliente_id = None
        servico_id = None
        data_inicio_convertida = None
        data_fim_convertida = None
        periodicidade = "unica"

    if not data_convertida:
        data_convertida = datetime.utcnow().date()

    lancamento = Venda(
        tipo=tipo,
        descricao=descricao,
        cliente_id=cliente_id,
        servico_id=servico_id,
        valor=valor,
        data=data_convertida,
        forma_pagamento=forma_pagamento,
        categoria="",
        status=status,
        observacoes=observacoes
    )

    if hasattr(lancamento, "data_inicio"):
        lancamento.data_inicio = data_inicio_convertida

    if hasattr(lancamento, "data_fim"):
        lancamento.data_fim = data_fim_convertida

    if hasattr(lancamento, "periodicidade"):
        lancamento.periodicidade = periodicidade

    db.session.add(lancamento)
    db.session.commit()

    flash("Lançamento cadastrado com sucesso.", "success")
    return redirect(url_for("vendas.vendas"))


@vendas_bp.route("/editar/<int:venda_id>", methods=["POST"])
@login_required
def editar_lancamento(venda_id):
    lancamento = Venda.query.get_or_404(venda_id)

    tipo = request.form.get("tipo", lancamento.tipo or "").strip()

    if tipo == "despesa":
        tipo = "custo"

    descricao = request.form.get("descricao", "").strip()
    cliente_id = converter_inteiro(request.form.get("cliente_id", "").strip())
    servico_id = converter_inteiro(request.form.get("servico_id", "").strip())
    valor = request.form.get("valor", "0").strip().replace(",", ".")
    data = request.form.get("data", "").strip()
    data_inicio = request.form.get("data_inicio", "").strip()
    data_fim = request.form.get("data_fim", "").strip()
    periodicidade = request.form.get("periodicidade", "unica").strip()
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    status = request.form.get("status", "pago").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if tipo not in ["receita", "custo"]:
        flash("Escolha uma aba válida para lançar receita ou custo.", "warning")
        return redirect(url_for("vendas.vendas"))

    if not descricao:
        flash("A descrição do lançamento é obrigatória.", "warning")
        return redirect(url_for("vendas.vendas"))

    try:
        valor = float(valor)
    except ValueError:
        flash("Informe um valor válido.", "warning")
        return redirect(url_for("vendas.vendas"))

    if valor <= 0:
        flash("O valor precisa ser maior que zero.", "warning")
        return redirect(url_for("vendas.vendas"))

    data_convertida = converter_data(data)
    data_inicio_convertida = converter_data(data_inicio)
    data_fim_convertida = converter_data(data_fim)

    if tipo == "receita":
        if not cliente_id:
            flash("Selecione um cliente para atualizar a receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if not servico_id:
            flash("Selecione um serviço para atualizar a receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if not data_inicio_convertida:
            flash("Informe a data de início do período da receita.", "warning")
            return redirect(url_for("vendas.vendas"))

        if periodicidade not in PERIODICIDADES_RECEITA:
            periodicidade = "unica"

        if periodicidade != "unica" and not data_fim_convertida:
            flash("Informe a data de fim para receitas periódicas.", "warning")
            return redirect(url_for("vendas.vendas"))

        if data_fim_convertida and data_fim_convertida < data_inicio_convertida:
            flash("A data de fim não pode ser anterior à data de início.", "warning")
            return redirect(url_for("vendas.vendas"))

        data_convertida = data_inicio_convertida

    if tipo == "custo":
        if not data_convertida:
            flash("Informe a data do custo.", "warning")
            return redirect(url_for("vendas.vendas"))

        cliente_id = None
        servico_id = None
        data_inicio_convertida = None
        data_fim_convertida = None
        periodicidade = "unica"

    if not data_convertida:
        data_convertida = datetime.utcnow().date()

    lancamento.tipo = tipo
    lancamento.descricao = descricao
    lancamento.cliente_id = cliente_id
    lancamento.servico_id = servico_id
    lancamento.valor = valor
    lancamento.data = data_convertida
    lancamento.forma_pagamento = forma_pagamento
    lancamento.categoria = ""
    lancamento.status = status
    lancamento.observacoes = observacoes

    if hasattr(lancamento, "data_inicio"):
        lancamento.data_inicio = data_inicio_convertida

    if hasattr(lancamento, "data_fim"):
        lancamento.data_fim = data_fim_convertida

    if hasattr(lancamento, "periodicidade"):
        lancamento.periodicidade = periodicidade

    db.session.commit()

    flash("Lançamento atualizado com sucesso.", "success")
    return redirect(url_for("vendas.vendas"))


@vendas_bp.route("/excluir/<int:venda_id>", methods=["POST"])
@login_required
def excluir_lancamento(venda_id):
    lancamento = Venda.query.get_or_404(venda_id)

    db.session.delete(lancamento)
    db.session.commit()

    flash("Lançamento excluído com sucesso.", "success")
    return redirect(url_for("vendas.vendas"))
