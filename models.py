from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base


class ProdutoDB(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)

class UnidadeDB(Base):
    __tablename__ = "unidades"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)

class EstoqueDB(Base):
    __tablename__ = "estoques"
    id = Column(Integer, primary_key=True, index=True)

    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False
    )

    unidade_id = Column(
        Integer,
        ForeignKey("unidades.id"),
        nullable=False
    )

    quantidade = Column(Integer, nullable=False)

class PedidoDB(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)

    unidade_id = Column(
        Integer,
        ForeignKey("unidades.id"),
        nullable=False

    )
    canal = Column(String, nullable=False)
    status = Column(String, nullable=False)

class ItemPedidoDB(Base):
    __tablename__ = "item_pedidos"
    id = Column(Integer, primary_key=True, index=True)

    pedido_id = Column(
        Integer,
        ForeignKey("pedidos.id"),
        nullable=False
    )
    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False
    )
    quantidade = Column(Integer, nullable=False)

class PagamentoDB(Base):
    __tablename__ = "pagamentos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(
        Integer,
        ForeignKey("pedidos.id"),
        nullable=False
    )
    status = Column(String, nullable=False)

class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome= Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)



