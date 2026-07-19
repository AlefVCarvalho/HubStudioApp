from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Contato, Produto, Producao, ProducaoProduto

producao_bp = Blueprint("producao", __name__, url_prefix="/producao")
ETAPAS = [("alinhamento", "Alinhamento"), ("materiais", "Materiais"), ("producao", "Produção"), ("ajustes", "Ajustes"), ("entrega", "Entrega")]

@producao_bp.route("/")
@login_required
def producao():
    producoes = Producao.query.order_by(Producao.id.desc()).all()
    grupos = {chave: [] for chave, _ in ETAPAS}
    for item in producoes: grupos.setdefault(item.etapa, []).append(item)
    return render_template("producao/index.html", etapas=ETAPAS, grupos=grupos, clientes=Contato.query.filter_by(fase="cliente").order_by(Contato.nome).all(), produtos=Produto.query.order_by(Produto.nome).all())


def preencher_produtos(producao):
    ids = request.form.getlist("produto_id[]")
    valores = request.form.getlist("produto_valor[]")
    periodicidades = request.form.getlist("produto_periodicidade[]")
    producao.produtos.clear()
    for i, produto_id in enumerate(ids):
        if not produto_id: continue
        try: valor = Decimal((valores[i] if i < len(valores) else "0").replace(",", "."))
        except InvalidOperation: valor = Decimal("0")
        periodicidade = periodicidades[i] if i < len(periodicidades) and periodicidades[i] in ["pontual", "mensal"] else "pontual"
        producao.produtos.append(ProducaoProduto(produto_id=int(produto_id), valor=valor, periodicidade=periodicidade))

@producao_bp.route("/novo", methods=["POST"])
@login_required
def novo():
    cliente_id = request.form.get("cliente_id", type=int)
    titulo = request.form.get("titulo", "").strip()
    if not cliente_id or not titulo:
        flash("Selecione o cliente e informe o nome do serviço.", "warning")
        return redirect(url_for("producao.producao"))
    item = Producao(cliente_id=cliente_id, titulo=titulo, descricao=request.form.get("descricao", "").strip(), observacoes=request.form.get("observacoes", "").strip(), etapa="alinhamento")
    preencher_produtos(item)
    if not item.produtos:
        flash("Vincule ao menos um produto.", "warning")
        return redirect(url_for("producao.producao"))
    db.session.add(item); db.session.commit(); flash("Serviço adicionado à produção.", "success")
    return redirect(url_for("producao.producao"))

@producao_bp.route("/editar/<int:producao_id>", methods=["POST"])
@login_required
def editar(producao_id):
    item = Producao.query.get_or_404(producao_id)
    item.cliente_id = request.form.get("cliente_id", type=int)
    item.titulo = request.form.get("titulo", "").strip()
    item.descricao = request.form.get("descricao", "").strip()
    item.observacoes = request.form.get("observacoes", "").strip()
    preencher_produtos(item); db.session.commit(); flash("Produção atualizada.", "success")
    return redirect(url_for("producao.producao"))

@producao_bp.route("/mover/<int:producao_id>", methods=["POST"])
@login_required
def mover(producao_id):
    item = Producao.query.get_or_404(producao_id)
    etapa = (request.get_json(silent=True) or {}).get("etapa")
    if etapa not in {e[0] for e in ETAPAS}: return jsonify(sucesso=False), 400
    item.etapa = etapa; db.session.commit(); return jsonify(sucesso=True)

@producao_bp.route("/excluir/<int:producao_id>", methods=["POST"])
@login_required
def excluir(producao_id):
    item = Producao.query.get_or_404(producao_id)
    db.session.delete(item); db.session.commit(); flash("Produção excluída.", "success")
    return redirect(url_for("producao.producao"))
