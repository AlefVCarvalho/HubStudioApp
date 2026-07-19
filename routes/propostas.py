from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from models import db, Contato

propostas_bp = Blueprint("propostas", __name__, url_prefix="/propostas")
ETAPAS = [("reuniao", "Reunião"), ("analise", "Análise"), ("proposta", "Proposta"), ("negociacao", "Negociação"), ("cliente", "Cliente")]

@propostas_bp.route("/")
@login_required
def propostas():
    contatos = Contato.query.filter_by(fase="proposta").order_by(Contato.nome).all()
    grupos = {chave: [] for chave, _ in ETAPAS}
    for contato in contatos:
        grupos.setdefault(contato.etapa_proposta or "reuniao", []).append(contato)
    return render_template("propostas/index.html", etapas=ETAPAS, grupos=grupos)

@propostas_bp.route("/mover/<int:contato_id>", methods=["POST"])
@login_required
def mover(contato_id):
    contato = Contato.query.get_or_404(contato_id)
    etapa = (request.get_json(silent=True) or {}).get("etapa")
    validas = {item[0] for item in ETAPAS}
    if etapa not in validas:
        return jsonify(sucesso=False), 400
    if etapa == "cliente":
        contato.fase = "cliente"; contato.etapa_proposta = None
        db.session.commit()
        return jsonify(sucesso=True, remover=True)
    contato.etapa_proposta = etapa
    db.session.commit()
    return jsonify(sucesso=True, remover=False)

@propostas_bp.route("/editar/<int:contato_id>", methods=["POST"])
@login_required
def editar(contato_id):
    contato = Contato.query.get_or_404(contato_id)
    for campo in ["nome", "descricao", "celular", "telefone", "email", "tags", "observacoes", "observacao_proposta"]:
        setattr(contato, campo, request.form.get(campo, "").strip())
    db.session.commit(); flash("Proposta atualizada.", "success")
    return redirect(url_for("propostas.propostas"))
