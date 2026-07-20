from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Contato, Produto, Producao, ProducaoProduto, ProducaoChecklist


producao_bp = Blueprint("producao", __name__, url_prefix="/producao")
ETAPAS = [
    ("alinhamento", "Alinhamento"),
    ("materiais", "Materiais"),
    ("producao", "Produção"),
    ("ajustes", "Ajustes"),
    ("entrega", "Entrega"),
]


@producao_bp.route("/")
@login_required
def producao():
    producoes = Producao.query.filter(Producao.etapa != "entrega").order_by(Producao.id.desc()).all()
    grupos = {chave: [] for chave, _ in ETAPAS}
    for item in producoes:
        grupos.setdefault(item.etapa, []).append(item)

    produtos = Produto.query.order_by(Produto.nome).all()
    produtos_json = {
        produto.id: [
            {"id": etapa.id, "descricao": etapa.descricao, "ordem": etapa.ordem}
            for etapa in produto.etapas
        ]
        for produto in produtos
    }

    return render_template(
        "producao/index.html",
        etapas=ETAPAS,
        grupos=grupos,
        clientes=Contato.query.filter_by(fase="cliente").order_by(Contato.nome).all(),
        produtos=produtos,
        produtos_json=produtos_json,
    )


def converter_valor(valor_texto):
    texto = (valor_texto or "0").strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(texto)
    except InvalidOperation:
        return Decimal("0")


def aplicar_produto(producao, produto_id, valor, periodicidade):
    produto = db.session.get(Produto, produto_id)
    if not produto:
        return False

    produto_anterior_id = producao.produto_item.produto_id if producao.produto_item else None
    producao.produtos.clear()
    producao.produtos.append(
        ProducaoProduto(
            produto_id=produto.id,
            valor=valor,
            periodicidade=periodicidade if periodicidade in {"pontual", "mensal"} else "pontual",
        )
    )

    if produto_anterior_id != produto.id or not producao.checklist:
        producao.checklist.clear()
        for etapa in produto.etapas:
            producao.checklist.append(
                ProducaoChecklist(
                    produto_etapa_id=etapa.id,
                    descricao=etapa.descricao,
                    ordem=etapa.ordem,
                    concluida=False,
                )
            )
    else:
        concluidas = {int(valor) for valor in request.form.getlist("checklist_concluido[]") if valor.isdigit()}
        for item in producao.checklist:
            item.concluida = item.id in concluidas

    return True


@producao_bp.route("/novo", methods=["POST"])
@login_required
def novo():
    cliente_id = request.form.get("cliente_id", type=int)
    titulo = request.form.get("titulo", "").strip()
    produto_id = request.form.get("produto_id", type=int)

    if not cliente_id or not titulo or not produto_id:
        flash("Selecione o cliente, informe o serviço e escolha um produto.", "warning")
        return redirect(url_for("producao.producao"))

    item = Producao(
        cliente_id=cliente_id,
        titulo=titulo,
        descricao=request.form.get("descricao", "").strip(),
        observacoes=request.form.get("observacoes", "").strip(),
        etapa="alinhamento",
        criado_em=datetime.utcnow(),
    )

    if not aplicar_produto(
        item,
        produto_id,
        converter_valor(request.form.get("produto_valor")),
        request.form.get("produto_periodicidade", "pontual"),
    ):
        flash("Produto inválido.", "warning")
        return redirect(url_for("producao.producao"))

    db.session.add(item)
    db.session.commit()
    flash("Serviço adicionado à produção.", "success")
    return redirect(url_for("producao.producao"))


@producao_bp.route("/editar/<int:producao_id>", methods=["POST"])
@login_required
def editar(producao_id):
    item = Producao.query.get_or_404(producao_id)
    cliente_id = request.form.get("cliente_id", type=int)
    produto_id = request.form.get("produto_id", type=int)
    titulo = request.form.get("titulo", "").strip()

    if not cliente_id or not produto_id or not titulo:
        flash("Cliente, serviço e produto são obrigatórios.", "warning")
        return redirect(url_for("producao.producao"))

    item.cliente_id = cliente_id
    item.titulo = titulo
    item.descricao = request.form.get("descricao", "").strip()
    item.observacoes = request.form.get("observacoes", "").strip()
    aplicar_produto(
        item,
        produto_id,
        converter_valor(request.form.get("produto_valor")),
        request.form.get("produto_periodicidade", "pontual"),
    )
    db.session.commit()
    flash("Produção atualizada.", "success")
    return redirect(url_for("producao.producao"))


@producao_bp.route("/mover/<int:producao_id>", methods=["POST"])
@login_required
def mover(producao_id):
    item = Producao.query.get_or_404(producao_id)
    etapa = (request.get_json(silent=True) or {}).get("etapa")
    if etapa not in {e[0] for e in ETAPAS}:
        return jsonify(sucesso=False), 400

    item.etapa = etapa
    item.concluido_em = datetime.utcnow() if etapa == "entrega" else None
    db.session.commit()
    return jsonify(sucesso=True, removido=etapa == "entrega")


@producao_bp.route("/excluir/<int:producao_id>", methods=["POST"])
@login_required
def excluir(producao_id):
    item = Producao.query.get_or_404(producao_id)
    db.session.delete(item)
    db.session.commit()
    flash("Produção excluída.", "success")
    return redirect(url_for("producao.producao"))
