from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import Usuario


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if not usuario or not senha:
            flash("Informe usuário e senha.", "warning")
            return redirect(url_for("auth.login"))

        usuario_db = Usuario.query.filter_by(usuario=usuario).first()

        if not usuario_db or not usuario_db.verificar_senha(senha):
            flash("Usuário ou senha inválidos.", "danger")
            return redirect(url_for("auth.login"))

        login_user(usuario_db)
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))