from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Cliente, Venda


clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.route("/")
@login_required
def clientes():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "").strip()

    query = Cliente.query

    if busca:
        query = query.filter(
            Cliente.nome.ilike(f"%{busca}%") |
            Cliente.cnpj.ilike(f"%{busca}%") |
            Cliente.telefone.ilike(f"%{busca}%") |
            Cliente.email.ilike(f"%{busca}%") |
            Cliente.tags.ilike(f"%{busca}%") |
            Cliente.responsavel.ilike(f"%{busca}%") |
            Cliente.responsavel_nome.ilike(f"%{busca}%") |
            Cliente.responsavel_celular.ilike(f"%{busca}%") |
            Cliente.responsavel_contato.ilike(f"%{busca}%")
        )

    if status == "ativo":
        query = query.filter(Cliente.ativo == True)
    elif status == "inativo":
        query = query.filter(Cliente.ativo == False)

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
            vendas_por_cliente.setdefault(venda.cliente_id, []).append(venda)

    return render_template(
        "clientes/index.html",
        clientes=lista_clientes,
        vendas_por_cliente=vendas_por_cliente,
        busca=busca,
        status=status
    )


@clientes_bp.route("/novo", methods=["POST"])
@login_required
def novo_cliente():
    nome = request.form.get("nome", "").strip()
    cnpj = request.form.get("cnpj", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email = request.form.get("email", "").strip()
    tags = request.form.get("tags", "").strip()
    observacoes = request.form.get("observacoes", "").strip()

    responsavel_nome = request.form.get("responsavel_nome", "").strip()
    responsavel_celular = request.form.get("responsavel_celular", "").strip()
    responsavel_contato = request.form.get("responsavel_contato", "").strip()

    if not nome:
        flash("O nome do cliente é obrigatório.", "warning")
        return redirect(url_for("clientes.clientes"))

    cliente = Cliente(
        nome=nome,
        cnpj=cnpj,
        telefone=telefone,
        email=email,
        tags=tags,
        observacoes=observacoes,
        responsavel=responsavel_nome,
        responsavel_nome=responsavel_nome,
        responsavel_celular=responsavel_celular,
        responsavel_contato=responsavel_contato,
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
    tags = request.form.get("tags", "").strip()
    observacoes = request.form.get("observacoes", "").strip()

    responsavel_nome = request.form.get("responsavel_nome", "").strip()
    responsavel_celular = request.form.get("responsavel_celular", "").strip()
    responsavel_contato = request.form.get("responsavel_contato", "").strip()

    ativo = request.form.get("ativo") == "on"

    if not nome:
        flash("O nome do cliente é obrigatório.", "warning")
        return redirect(url_for("clientes.clientes"))

    cliente.nome = nome
    cliente.cnpj = cnpj
    cliente.telefone = telefone
    cliente.email = email
    cliente.tags = tags
    cliente.observacoes = observacoes

    cliente.responsavel = responsavel_nome
    cliente.responsavel_nome = responsavel_nome
    cliente.responsavel_celular = responsavel_celular
    cliente.responsavel_contato = responsavel_contato

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
