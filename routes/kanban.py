from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required

from models import db, Cliente


kanban_bp = Blueprint("kanban", __name__, url_prefix="/kanban")


KANBAN_ETAPAS = [
    {
        "id": "prospeccao",
        "nome": "Prospecção",
        "descricao": "Cliente em fase inicial de abordagem."
    },
    {
        "id": "contato_feito",
        "nome": "Contato feito",
        "descricao": "Primeiro contato já realizado."
    },
    {
        "id": "diagnostico",
        "nome": "Diagnóstico",
        "descricao": "Entendimento da necessidade do cliente."
    },
    {
        "id": "proposta_enviada",
        "nome": "Proposta enviada",
        "descricao": "Proposta comercial enviada ao cliente."
    },
    {
        "id": "negociacao",
        "nome": "Negociação",
        "descricao": "Ajustes finais antes do fechamento."
    },
]


KANBAN_STATUS_VALIDOS = [etapa["id"] for etapa in KANBAN_ETAPAS]


@kanban_bp.route("/")
@login_required
def kanban():
    clientes_disponiveis = (
        Cliente.query
        .filter(Cliente.ativo == False)
        .filter((Cliente.status == "-") | (Cliente.status == None))
        .order_by(Cliente.nome.asc())
        .all()
    )

    clientes_por_etapa = {}

    for etapa in KANBAN_ETAPAS:
        clientes_por_etapa[etapa["id"]] = (
            Cliente.query
            .filter(Cliente.ativo == False)
            .filter(Cliente.status == etapa["id"])
            .order_by(Cliente.atualizado_em.desc(), Cliente.nome.asc())
            .all()
        )

    return render_template(
        "kanban.html",
        etapas=KANBAN_ETAPAS,
        clientes_por_etapa=clientes_por_etapa,
        clientes_disponiveis=clientes_disponiveis
    )


@kanban_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_ao_kanban():
    cliente_id = request.form.get("cliente_id", "").strip()

    if not cliente_id:
        flash("Selecione um cliente para adicionar ao kanban.", "warning")
        return redirect(url_for("kanban.kanban"))

    cliente = Cliente.query.get_or_404(cliente_id)

    if cliente.ativo:
        flash("Este cliente já está ativo e disponível para vendas.", "warning")
        return redirect(url_for("kanban.kanban"))

    cliente.status = "prospeccao"
    cliente.ativo = False

    db.session.commit()

    flash("Cliente adicionado ao kanban.", "success")
    return redirect(url_for("kanban.kanban"))


@kanban_bp.route("/mover/<int:cliente_id>", methods=["POST"])
@login_required
def mover_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "").strip()

    if novo_status == "fechado":
        cliente.status = "ativo"
        cliente.ativo = True

        db.session.commit()

        return jsonify({
            "sucesso": True,
            "remover_card": True,
            "mensagem": "Cliente fechado e ativado com sucesso."
        })

    if novo_status not in KANBAN_STATUS_VALIDOS:
        return jsonify({
            "sucesso": False,
            "mensagem": "Status inválido."
        }), 400

    cliente.status = novo_status
    cliente.ativo = False

    db.session.commit()

    return jsonify({
        "sucesso": True,
        "remover_card": False,
        "mensagem": "Cliente movido com sucesso."
    })


@kanban_bp.route("/remover/<int:cliente_id>", methods=["POST"])
@login_required
def remover_do_kanban(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if cliente.ativo:
        flash("Clientes ativos não podem voltar para fora do kanban por esta ação.", "warning")
        return redirect(url_for("kanban.kanban"))

    cliente.status = "-"
    db.session.commit()

    flash("Cliente removido do kanban.", "success")
    return redirect(url_for("kanban.kanban"))