from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False, default="Administrador")
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.usuario}>"


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    responsavel = db.Column(db.String(120), nullable=True)

    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    servicos = db.relationship(
        "ClienteServico",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )

    vendas = db.relationship(
        "Venda",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Cliente {self.nome}>"


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(150), nullable=False)
    periodicidade = db.Column(db.String(50), nullable=True)
    valor = db.Column(db.Float, nullable=False, default=0.0)
    tempo_medio = db.Column(db.String(80), nullable=True)
    descricao = db.Column(db.Text, nullable=True)

    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    clientes = db.relationship(
        "ClienteServico",
        back_populates="servico",
        cascade="all, delete-orphan"
    )

    vendas = db.relationship(
        "Venda",
        back_populates="servico"
    )

    def __repr__(self):
        return f"<Servico {self.nome}>"


class ClienteServico(db.Model):
    __tablename__ = "cliente_servico"

    id = db.Column(db.Integer, primary_key=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=False
    )

    servico_id = db.Column(
        db.Integer,
        db.ForeignKey("servicos.id"),
        nullable=False
    )

    valor_personalizado = db.Column(db.Float, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship(
        "Cliente",
        back_populates="servicos"
    )

    servico = db.relationship(
        "Servico",
        back_populates="clientes"
    )

    def valor_final(self):
        if self.valor_personalizado is not None:
            return self.valor_personalizado

        return self.servico.valor

    def __repr__(self):
        return f"<ClienteServico cliente={self.cliente_id} servico={self.servico_id}>"


class Venda(db.Model):
    __tablename__ = "vendas"

    id = db.Column(db.Integer, primary_key=True)

    tipo = db.Column(db.String(20), nullable=False)
    # Valores esperados:
    # receita
    # despesa

    descricao = db.Column(db.String(255), nullable=False)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id"),
        nullable=True
    )

    servico_id = db.Column(
        db.Integer,
        db.ForeignKey("servicos.id"),
        nullable=True
    )

    valor = db.Column(db.Float, nullable=False, default=0.0)

    data = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    forma_pagamento = db.Column(db.String(80), nullable=True)

    categoria = db.Column(db.String(100), nullable=True)
    # Para receitas: venda, mensalidade, serviço avulso etc.
    # Para despesas: aluguel, internet, imposto, funcionário, marketing etc.

    status = db.Column(db.String(50), nullable=False, default="pago")
    # pago
    # pendente
    # cancelado

    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    cliente = db.relationship(
        "Cliente",
        back_populates="vendas"
    )

    servico = db.relationship(
        "Servico",
        back_populates="vendas"
    )

    def __repr__(self):
        return f"<Venda {self.tipo} - {self.descricao} - R$ {self.valor}>"