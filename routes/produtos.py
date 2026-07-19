from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Produto, ProdutoEtapa

produtos_bp = Blueprint("produtos", __name__, url_prefix="/produtos")

@produtos_bp.route("/")
@login_required
def produtos():
    busca = request.args.get("busca", "").strip()
    tag = request.args.get("tag", "").strip()
    query = Produto.query
    if busca:
        query = query.filter(Produto.nome.ilike(f"%{busca}%") | Produto.descricao.ilike(f"%{busca}%"))
    if tag:
        query = query.filter(Produto.tags.ilike(f"%{tag}%"))
    lista = query.order_by(Produto.nome).all()
    return render_template("produtos/index.html", produtos=lista, busca=busca, tag=tag)


def salvar_etapas(produto):
    descricoes = request.form.getlist("etapas[]")
    produto.etapas.clear()
    for ordem, descricao in enumerate(descricoes):
        descricao = descricao.strip()
        if descricao:
            produto.etapas.append(ProdutoEtapa(descricao=descricao, ordem=ordem))

@produtos_bp.route("/novo", methods=["POST"])
@login_required
def novo():
    nome = request.form.get("nome", "").strip()
    if not nome:
        flash("Informe o nome do produto.", "warning")
        return redirect(url_for("produtos.produtos"))
    produto = Produto(nome=nome, descricao=request.form.get("descricao", "").strip(), tags=request.form.get("tags", "").strip())
    salvar_etapas(produto)
    db.session.add(produto)
    db.session.commit()
    flash("Produto criado com sucesso.", "success")
    return redirect(url_for("produtos.produtos"))

@produtos_bp.route("/editar/<int:produto_id>", methods=["POST"])
@login_required
def editar(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    produto.nome = request.form.get("nome", "").strip()
    produto.descricao = request.form.get("descricao", "").strip()
    produto.tags = request.form.get("tags", "").strip()
    salvar_etapas(produto)
    db.session.commit()
    flash("Produto atualizado.", "success")
    return redirect(url_for("produtos.produtos"))

@produtos_bp.route("/excluir/<int:produto_id>", methods=["POST"])
@login_required
def excluir(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if produto.itens_producao:
        flash("Este produto está vinculado a uma produção e não pode ser excluído.", "warning")
    else:
        db.session.delete(produto)
        db.session.commit()
        flash("Produto excluído.", "success")
    return redirect(url_for("produtos.produtos"))
