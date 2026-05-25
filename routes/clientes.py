from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Cliente, Venda


clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.route("/")
@login_required
def clientes():
    busca = request.args.get("busca", "").strip()

    query = Cliente.query

    if busca:
        query = query.filter(
            Cliente.nome.ilike(f"%{busca}%") |
            Cliente.cnpj.ilike(f"%{busca}%") |
            Cliente.email.ilike(f"%{busca}%") |
            Cliente.responsavel.ilike(f"%{busca}%")
        )

    lista_clientes = query.order_by(Cliente.nome.asc()).all()

    cliente_ids = [cliente.id for cliente in lista_clientes]

    vendas_por_cliente = {}

    if cliente_ids:
        vendas = (
            Venda.query
            .filter(Venda.cliente_id.in_(cliente_ids))
            .order_by(Venda.data.desc(), Venda.id.desc())
            .all()
        )

        for venda in vendas:
            if venda.cliente_id not in vendas_por_cliente:
                vendas_por_cliente[venda.cliente_id] = []

            vendas_por_cliente[venda.cliente_id].append(venda)

    return render_template(
        "clientes/index.html",
        clientes=lista_clientes,
        busca=busca,
        vendas_por_cliente=vendas_por_cliente
    )


@clientes_bp.route("/novo", methods=["POST"])
@login_required
def novo_cliente():
    nome = request.form.get("nome", "").strip()
    cnpj = request.form.get("cnpj", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email = request.form.get("email", "").strip()
    responsavel = request.form.get("responsavel", "").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if not nome:
        flash("O nome do cliente é obrigatório.", "warning")
        return redirect(url_for("clientes.clientes"))

    cliente = Cliente(
        nome=nome,
        cnpj=cnpj,
        telefone=telefone,
        email=email,
        responsavel=responsavel,
        observacoes=observacoes,
        ativo=True
    )

    db.session.add(cliente)
    db.session.commit()

    flash("Cliente cadastrado com sucesso.", "success")
    return redirect(url_for("clientes.clientes"))


@clientes_bp.route("/editar/<int:cliente_id>", methods=["POST"])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    nome = request.form.get("nome", "").strip()
    cnpj = request.form.get("cnpj", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email = request.form.get("email", "").strip()
    responsavel = request.form.get("responsavel", "").strip()
    observacoes = request.form.get("observacoes", "").strip()
    ativo = request.form.get("ativo") == "on"

    if not nome:
        flash("O nome do cliente é obrigatório.", "warning")
        return redirect(url_for("clientes.clientes"))

    cliente.nome = nome
    cliente.cnpj = cnpj
    cliente.telefone = telefone
    cliente.email = email
    cliente.responsavel = responsavel
    cliente.observacoes = observacoes
    cliente.ativo = ativo

    db.session.commit()

    flash("Cliente atualizado com sucesso.", "success")
    return redirect(url_for("clientes.clientes"))


@clientes_bp.route("/excluir/<int:cliente_id>", methods=["POST"])
@login_required
def excluir_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    db.session.delete(cliente)
    db.session.commit()

    flash("Cliente excluído com sucesso.", "success")
    return redirect(url_for("clientes.clientes"))