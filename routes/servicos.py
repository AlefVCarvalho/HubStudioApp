from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models import db, Servico


servicos_bp = Blueprint("servicos", __name__, url_prefix="/servicos")


@servicos_bp.route("/")
@login_required
def servicos():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "").strip()

    query = Servico.query

    if busca:
        query = query.filter(
            Servico.nome.ilike(f"%{busca}%") |
            Servico.descricao.ilike(f"%{busca}%") |
            Servico.tags.ilike(f"%{busca}%")
        )

    if status == "ativo":
        query = query.filter(Servico.ativo == True)
    elif status == "inativo":
        query = query.filter(Servico.ativo == False)

    lista_servicos = query.order_by(Servico.nome.asc()).all()

    return render_template(
        "servicos.html",
        servicos=lista_servicos,
        busca=busca,
        status=status
    )


@servicos_bp.route("/novo", methods=["POST"])
@login_required
def novo_servico():
    nome = request.form.get("nome", "").strip()
    tags = request.form.get("tags", "").strip()
    descricao = request.form.get("descricao", "").strip()

    if not nome:
        flash("O nome do serviço é obrigatório.", "warning")
        return redirect(url_for("servicos.servicos"))

    servico = Servico(
        nome=nome,
        tags=tags,
        descricao=descricao,
        ativo=True
    )

    db.session.add(servico)
    db.session.commit()

    flash("Serviço cadastrado com sucesso.", "success")
    return redirect(url_for("servicos.servicos"))


@servicos_bp.route("/editar/<int:servico_id>", methods=["POST"])
@login_required
def editar_servico(servico_id):
    servico = Servico.query.get_or_404(servico_id)

    nome = request.form.get("nome", "").strip()
    tags = request.form.get("tags", "").strip()
    descricao = request.form.get("descricao", "").strip()
    ativo = request.form.get("ativo") == "on"

    if not nome:
        flash("O nome do serviço é obrigatório.", "warning")
        return redirect(url_for("servicos.servicos"))

    servico.nome = nome
    servico.tags = tags
    servico.descricao = descricao
    servico.ativo = ativo

    db.session.commit()

    flash("Serviço atualizado com sucesso.", "success")
    return redirect(url_for("servicos.servicos"))


@servicos_bp.route("/excluir/<int:servico_id>", methods=["POST"])
@login_required
def excluir_servico(servico_id):
    servico = Servico.query.get_or_404(servico_id)

    db.session.delete(servico)
    db.session.commit()

    flash("Serviço excluído com sucesso.", "success")
    return redirect(url_for("servicos.servicos"))
