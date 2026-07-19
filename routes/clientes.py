from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Contato

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

@clientes_bp.route("/")
@login_required
def clientes():
    busca = request.args.get("busca", "").strip(); tag = request.args.get("tag", "").strip()
    query = Contato.query.filter_by(fase="cliente")
    if busca:
        query = query.filter(Contato.nome.ilike(f"%{busca}%") | Contato.email.ilike(f"%{busca}%") | Contato.celular.ilike(f"%{busca}%"))
    if tag:
        query = query.filter(Contato.tags.ilike(f"%{tag}%"))
    return render_template("clientes/index.html", clientes=query.order_by(Contato.nome).all(), busca=busca, tag=tag)

@clientes_bp.route("/editar/<int:cliente_id>", methods=["POST"])
@login_required
def editar(cliente_id):
    cliente = Contato.query.get_or_404(cliente_id)
    for campo in ["nome", "descricao", "celular", "telefone", "email", "tags", "observacoes"]:
        setattr(cliente, campo, request.form.get(campo, "").strip())
    db.session.commit(); flash("Cliente atualizado.", "success")
    return redirect(url_for("clientes.clientes"))
