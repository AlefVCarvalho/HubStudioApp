from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Contato

prospeccoes_bp = Blueprint("prospeccoes", __name__, url_prefix="/prospeccoes")

@prospeccoes_bp.route("/")
@login_required
def prospeccoes():
    busca = request.args.get("busca", "").strip()
    tag = request.args.get("tag", "").strip()
    query = Contato.query.filter_by(fase="prospeccao")
    if busca:
        query = query.filter(Contato.nome.ilike(f"%{busca}%") | Contato.email.ilike(f"%{busca}%") | Contato.celular.ilike(f"%{busca}%"))
    if tag:
        query = query.filter(Contato.tags.ilike(f"%{tag}%"))
    return render_template("prospeccoes/index.html", contatos=query.order_by(Contato.nome).all(), busca=busca, tag=tag)


def preencher(contato):
    for campo in ["nome", "descricao", "celular", "telefone", "email", "tags", "observacoes"]:
        setattr(contato, campo, request.form.get(campo, "").strip())

@prospeccoes_bp.route("/novo", methods=["POST"])
@login_required
def novo():
    contato = Contato(fase="prospeccao")
    preencher(contato)
    if not contato.nome:
        flash("Informe o nome do contato.", "warning")
    else:
        db.session.add(contato); db.session.commit(); flash("Contato cadastrado.", "success")
    return redirect(url_for("prospeccoes.prospeccoes"))

@prospeccoes_bp.route("/editar/<int:contato_id>", methods=["POST"])
@login_required
def editar(contato_id):
    contato = Contato.query.get_or_404(contato_id)
    preencher(contato); db.session.commit(); flash("Contato atualizado.", "success")
    return redirect(url_for("prospeccoes.prospeccoes"))

@prospeccoes_bp.route("/enviar/<int:contato_id>", methods=["POST"])
@login_required
def enviar(contato_id):
    contato = Contato.query.get_or_404(contato_id)
    contato.fase = "proposta"; contato.etapa_proposta = "reuniao"
    db.session.commit(); flash("Contato enviado para Propostas.", "success")
    return redirect(url_for("prospeccoes.prospeccoes"))

@prospeccoes_bp.route("/excluir/<int:contato_id>", methods=["POST"])
@login_required
def excluir(contato_id):
    contato = Contato.query.get_or_404(contato_id)
    db.session.delete(contato); db.session.commit(); flash("Contato excluído.", "success")
    return redirect(url_for("prospeccoes.prospeccoes"))
