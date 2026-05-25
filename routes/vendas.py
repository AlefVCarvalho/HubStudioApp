from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Venda, Cliente, Servico


vendas_bp = Blueprint("vendas", __name__, url_prefix="/vendas")


@vendas_bp.route("/")
@login_required
def vendas():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "").strip()

    query = Venda.query

    if busca:
        query = query.filter(
            Venda.descricao.ilike(f"%{busca}%") |
            Venda.forma_pagamento.ilike(f"%{busca}%")
        )

    if status:
        query = query.filter(Venda.status == status)

    receitas = (
        query
        .filter(Venda.tipo == "receita")
        .order_by(Venda.data.desc(), Venda.id.desc())
        .all()
    )

    despesas = (
        query
        .filter(Venda.tipo == "despesa")
        .order_by(Venda.data.desc(), Venda.id.desc())
        .all()
    )

    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome.asc()).all()
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome.asc()).all()

    total_receitas = sum(venda.valor for venda in receitas if venda.status != "cancelado")
    total_despesas = sum(venda.valor for venda in despesas if venda.status != "cancelado")
    saldo = total_receitas - total_despesas

    return render_template(
        "vendas.html",
        receitas=receitas,
        despesas=despesas,
        clientes=clientes,
        servicos=servicos,
        busca=busca,
        status=status,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=saldo
    )


@vendas_bp.route("/novo", methods=["POST"])
@login_required
def novo_lancamento():
    tipo = request.form.get("tipo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    cliente_id = request.form.get("cliente_id", "").strip()
    servico_id = request.form.get("servico_id", "").strip()
    valor = request.form.get("valor", "0").strip().replace(",", ".")
    data = request.form.get("data", "").strip()
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    status = request.form.get("status", "pago").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if tipo not in ["receita", "despesa"]:
        flash("Escolha uma aba válida para lançar receita ou despesa.", "warning")
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

    try:
        data_convertida = datetime.strptime(data, "%Y-%m-%d").date()
    except ValueError:
        data_convertida = datetime.utcnow().date()

    cliente_id = int(cliente_id) if cliente_id else None
    servico_id = int(servico_id) if servico_id else None

    if tipo == "despesa":
        cliente_id = None
        servico_id = None

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

    db.session.add(lancamento)
    db.session.commit()

    flash("Lançamento cadastrado com sucesso.", "success")
    return redirect(url_for("vendas.vendas"))


@vendas_bp.route("/editar/<int:venda_id>", methods=["POST"])
@login_required
def editar_lancamento(venda_id):
    lancamento = Venda.query.get_or_404(venda_id)

    tipo = request.form.get("tipo", lancamento.tipo or "").strip()
    descricao = request.form.get("descricao", "").strip()
    cliente_id = request.form.get("cliente_id", "").strip()
    servico_id = request.form.get("servico_id", "").strip()
    valor = request.form.get("valor", "0").strip().replace(",", ".")
    data = request.form.get("data", "").strip()
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    status = request.form.get("status", "pago").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if tipo not in ["receita", "despesa"]:
        flash("Escolha uma aba válida para lançar receita ou despesa.", "warning")
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

    try:
        data_convertida = datetime.strptime(data, "%Y-%m-%d").date()
    except ValueError:
        data_convertida = datetime.utcnow().date()

    cliente_id = int(cliente_id) if cliente_id else None
    servico_id = int(servico_id) if servico_id else None

    if tipo == "despesa":
        cliente_id = None
        servico_id = None

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
