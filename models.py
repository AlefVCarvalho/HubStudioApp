from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False, default="Administrador")
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Produto(db.Model):
    __tablename__ = "produtos"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    tags = db.Column(db.String(255))
    etapas = db.relationship("ProdutoEtapa", back_populates="produto", cascade="all, delete-orphan", order_by="ProdutoEtapa.ordem")
    itens_producao = db.relationship("ProducaoProduto", back_populates="produto")


class ProdutoEtapa(db.Model):
    __tablename__ = "produto_etapas"
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    produto = db.relationship("Produto", back_populates="etapas")


class Contato(db.Model):
    __tablename__ = "contatos"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    celular = db.Column(db.String(30))
    telefone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    tags = db.Column(db.String(255))
    observacoes = db.Column(db.Text)
    fase = db.Column(db.String(30), nullable=False, default="prospeccao")
    etapa_proposta = db.Column(db.String(30))
    observacao_proposta = db.Column(db.Text)
    producoes = db.relationship("Producao", back_populates="cliente", cascade="all, delete-orphan")


class Producao(db.Model):
    __tablename__ = "producoes"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("contatos.id", ondelete="CASCADE"), nullable=False)
    titulo = db.Column(db.String(180), nullable=False)
    descricao = db.Column(db.Text)
    etapa = db.Column(db.String(30), nullable=False, default="alinhamento")
    observacoes = db.Column(db.Text)
    cliente = db.relationship("Contato", back_populates="producoes")
    produtos = db.relationship("ProducaoProduto", back_populates="producao", cascade="all, delete-orphan")

    @property
    def valor_mensal(self):
        return sum(item.valor or 0 for item in self.produtos if item.periodicidade == "mensal")

    @property
    def valor_pontual(self):
        return sum(item.valor or 0 for item in self.produtos if item.periodicidade == "pontual")


class ProducaoProduto(db.Model):
    __tablename__ = "producao_produtos"
    id = db.Column(db.Integer, primary_key=True)
    producao_id = db.Column(db.Integer, db.ForeignKey("producoes.id", ondelete="CASCADE"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    periodicidade = db.Column(db.String(20), nullable=False, default="pontual")
    producao = db.relationship("Producao", back_populates="produtos")
    produto = db.relationship("Produto", back_populates="itens_producao")
