from fastapi import FastAPI, HTTPException,Depends
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from enum import Enum

from database import Base, engine, SessionLocal
import models
from pwdlib import PasswordHash
import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException,Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

security = HTTPBearer()
load_dotenv()
password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Produto(BaseModel):
    nome: str
    preco: float = Field(gt=0)
    quantidade: int = Field(ge=0)

class ProdutoAtualizacao(BaseModel):
    nome: str | None = None
    preco: float | None = Field(default= None, gt=0)
    quantidade: int | None = Field(default= None, ge=0)

class Unidade(BaseModel):
    nome: str
    endereco: str

class Estoque(BaseModel):
    produto_id: int = Field(gt=0)
    unidade_id: int = Field(gt=0)
    quantidade: int = Field(ge=0)

class ReposicaoEstoque(BaseModel):
    quantidade: int = Field(gt=0)

class CanalPedido(str, Enum):
    APP = 'APP'
    TOTEM = 'TOTEM'
    BALCAO = 'BALCAO'
    PICKUP = 'PICKUP'
    WEB = 'WEB'

class ItemPedidoEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)

class PedidoEntrada(BaseModel):
    unidade_id: int
    canalPedido: CanalPedido
    itens: list[ItemPedidoEntrada]

class PagamentoEntrada(BaseModel):
    pedido_id: int
    aprovado: bool

class RoleUsuario(str, Enum):
    ADMIN = 'ADMIN'
    CLIENTE = 'CLIENTE'

class UsuarioEntrada(BaseModel):
    nome: str
    email: str
    senha: str
    role: RoleUsuario

class LoginEntrada(BaseModel):
    email: str
    senha: str

def criar_token(usuario):
    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    dados_token = {
        'sub': str(usuario.id),
        'role': usuario.role,
        'exp': expiracao
    }
    token = jwt.encode(
        dados_token,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

def usuario_atual(
        credenciais: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    token = credenciais.credentials

    try:
        dados = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        usuario_id = int(dados['sub'])

    except Exception:
        raise HTTPException(
            status_code=401,
            detail= 'Token inválido ou expirado'
        )
    usuario = db.get(
        models.UsuarioDB,
        usuario_id
    )
    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail = 'Usuario não encontrado'
        )
    return usuario

def somente_admin(
        usuario = Depends(usuario_atual),
):
    if usuario.role != 'ADMIN':
        raise HTTPException(
            status_code=403,
            detail='Acesso permitido apenas papa administradores'
        )
    return usuario

@app.get('/usuarios/me')
def meu_perfil(
        usuario= Depends(usuario_atual),
):
    return {
        'id': usuario.id,
        'nome': usuario.nome,
        'email': usuario.email,
        'role': usuario.role,
    }

@app.get("/")
def inicio():
    return {"message": "API Raízes do Nordeste funcionando"}

@app.get("/produtos")
def listar_produtos(db: Session=Depends(get_db)):
    produtos_banco = db.scalars(
        select(models.ProdutoDB)
    ).all()

    return produtos_banco

@app.get("/produtos/{id_produto}")
def buscar_produto(
        id_produto: int,
        db: Session = Depends(get_db)
):
    produto = db.get(models.ProdutoDB, id_produto)

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
    )

    return produto

@app.get('/unidades')
def listar_unidades(
    db: Session = Depends(get_db)
):
    unidade= db.scalars(
        select(models.UnidadeDB)
    ).all()

    return unidade

@app.get('/estoques')
def listar_estoques(
        db: Session = Depends(get_db)
):
    estoques = db.scalars(
        select(models.EstoqueDB)
    ).all()
    return estoques

@app.patch('/estoques/{id_estoque}')
def repor_estoques(
        id_estoque: int,
        dados: ReposicaoEstoque,
        db: Session = Depends(get_db),
        usuario = Depends(somente_admin)
):
    estoque = db.get(
        models.EstoqueDB,
        id_estoque
    )
    if estoque is None:
        raise HTTPException(
            status_code=404,
            detail='Estoque não encontrado'
        )
    estoque.quantidade += dados.quantidade

    db.commit()
    db.refresh(estoque)
    return estoque


@app.post('/produtos', status_code=201)
def criar_produto(
        produto: Produto,
        db: Session = Depends(get_db)

):
    produto_existente = db.scalars(
        select(models.ProdutoDB).where(
            models.ProdutoDB.nome == produto.nome
        )
    ).first()
    if produto_existente is not None:
        raise HTTPException(
            status_code=409,
            detail= 'Produto já cadastrado'
        )

    novo_produto = models.ProdutoDB(
        nome=produto.nome,
        preco=produto.preco,
        quantidade=produto.quantidade
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@app.post('/unidades', status_code=201)
def criar_unidade(
        unidade: Unidade,
        db: Session = Depends(get_db)
):
    nova_unidade = models.UnidadeDB(
        nome=unidade.nome,
        endereco=unidade.endereco
    )
    db.add(nova_unidade)
    db.commit()
    db.refresh(nova_unidade)

    return nova_unidade

@app.post('/estoques',status_code=201)
def criar_estoque(
    estoque: Estoque,
    db: Session = Depends(get_db)
):
    produto = db.get(
        models.ProdutoDB,
        estoque.produto_id
    )
    if produto is None:
        raise HTTPException(
            status_code=404,
            detail='Produto não encontrado'
        )

    unidade = db.get(
        models.UnidadeDB,
        estoque.unidade_id
    )
    if unidade is None:
        raise HTTPException(
            status_code=404,
            detail="Unidade não encontrada"
        )

    estoque_existente = db.scalars(
        select(models.EstoqueDB).where(
            models.EstoqueDB.produto_id == estoque.produto_id,
            models.EstoqueDB.unidade_id == estoque.unidade_id
        )
    ).first()
    if estoque_existente is not None:
        raise HTTPException(
            status_code=409,
            detail= 'Estoque já cadastrado para este produto nesta unidade'
        )

    novo_estoque = models.EstoqueDB(
        produto_id=estoque.produto_id,
        unidade_id=estoque.unidade_id,
        quantidade=estoque.quantidade
    )
    db.add(novo_estoque)
    db.commit()
    db.refresh(novo_estoque)

    return novo_estoque

@app.delete('/produtos/{id_produto}')
def deletar_produto(
        id_produto: int,
        db: Session = Depends(get_db)
):
    produto = db.get(models.ProdutoDB, id_produto)
    if produto is None:
        raise HTTPException(
            status_code=404,
            detail= 'Produto não encontrado'
    )
    db.delete(produto)
    db.commit()
    return {
        "mensagem": "Produto deletado com sucesso"
    }

@app.delete('/estoques/{id_estoque}')
def deletar_estoque(
        id_estoque: int,
        db: Session = Depends(get_db)
):
    estoque = db.get(models.EstoqueDB, id_estoque)
    if estoque is None:
        raise HTTPException(
            status_code=404,
            detail= 'Estoque não encontrado'
        )
    db.delete(estoque)
    db.commit()
    return {
        'mensagem': 'Estoque deletado com sucesso'
    }

@app.patch("/produtos/{id_produto}")
def atualizar_produto(
        id_produto: int,
        dados: ProdutoAtualizacao,
        db: Session = Depends(get_db)
):
    produto = db.get(models.ProdutoDB, id_produto)

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    if dados.nome is not None:
        produto.nome = dados.nome

    if dados.preco is not None:
        produto.preco = dados.preco

    if dados.quantidade is not None:
        produto.quantidade = dados.quantidade

    db.commit()
    db.refresh(produto)

    return produto


@app.post('/pedidos', status_code=201)
def criar_pedido(
        pedido: PedidoEntrada,
        db: Session = Depends(get_db)
):
    estoques_validados = []
    produtos_no_pedido = set()

    unidade = db.get(
        models.UnidadeDB,
        pedido.unidade_id
    )

    if unidade is None:
        raise HTTPException(
            status_code=404,
            detail='Unidade não encontrada'
        )

    for item in pedido.itens:

        if item.produto_id in produtos_no_pedido:
            raise HTTPException(
                status_code=400,
                detail='Produto repetido no pedido'
            )
        produtos_no_pedido.add(item.produto_id)

        produto = db.get(
            models.ProdutoDB,
            item.produto_id
        )

        if produto is None:
            raise HTTPException(
                status_code=404,
                detail='Produto não encontrado'
            )

        estoque = db.scalars(
            select(models.EstoqueDB).where(
                models.EstoqueDB.produto_id == item.produto_id,
                models.EstoqueDB.unidade_id == pedido.unidade_id
            )
        ).first()

        if estoque is None:
            raise HTTPException(
                status_code=404,
                detail='Estoque não encontrado para este produto nesta unidade'
            )

        if estoque.quantidade < item.quantidade:
            raise HTTPException(
                status_code=409,
                detail='Estoque insuficiente'
            )

        estoques_validados.append((item, estoque))

    novo_pedido = models.PedidoDB(
        unidade_id=pedido.unidade_id,
        canal=pedido.canalPedido.value,
        status="CRIADO"
    )

    db.add(novo_pedido)
    db.flush()

    for item, estoque in estoques_validados:
        novo_item = models.ItemPedidoDB(
            pedido_id=novo_pedido.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade
        )
        db.add(novo_item)
        estoque.quantidade -= item.quantidade



    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido

@app.post('/pagamentos', status_code=201)
def realizar_pagamento(
        pagamento: PagamentoEntrada,
        db: Session = Depends(get_db)
):
    pedido = db.get(
        models.PedidoDB,
        pagamento.pedido_id
    )

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail= 'Pedido não encontrado'
        )
    pagamento_existente = db.scalars(
        select(models.PagamentoDB).where(
            models.PagamentoDB.pedido_id == pagamento.pedido_id,
        )
    ).first()

    if pagamento_existente is not None:
        raise HTTPException(
            status_code=409,
            detail= 'pagamento já registrado para este pedido'
        )
    if pagamento.aprovado:
        status_pagamento = 'APROVADO'
        pedido.status = 'PAGO'
    else:
        status_pagamento = 'RECUSADO'
        pedido.status = 'PAGAMENTO RECUSADO'

    novo_pagamento = models.PagamentoDB(
        pedido_id=pagamento.pedido_id,
        status=status_pagamento
    )
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)

    return novo_pagamento

@app.get('/pedidos/{id_pedido}')
def buscar_pedido(
        id_pedido: int,
        db: Session = Depends(get_db)
):
    pedido = db.get(
        models.PedidoDB,
        id_pedido
    )
    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail='Pedido não encontrado'
        )
    return pedido

@app.get('/pedidos')
def listar_pedidos(
    canalPedido: CanalPedido | None = None,
    db: Session = Depends(get_db)
):
    consulta = select(models.PedidoDB)

    if canalPedido is not None:
        consulta = consulta.where(
            models.PedidoDB.canal == canalPedido.value
        )
    pedidos = db.scalars(consulta).all()
    return pedidos

@app.post('/usuarios', status_code=201)
def criar_usuario(
        usuario: UsuarioEntrada,
        db: Session = Depends(get_db)
):
    usuario_existente = db.scalars(
        select(models.UsuarioDB).where(
            models.UsuarioDB.email == usuario.email
        )
    ).first()

    if usuario_existente is not None:
        raise HTTPException(
            status_code=409,
            detail= 'E-mail já cadastrado'
        )
    senha_protegida = password_hash.hash(usuario.senha)

    novo_usuario = models.UsuarioDB(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_protegida,
        role=usuario.role.value
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        'id': novo_usuario.id,
        'nome': novo_usuario.nome,
        'email': novo_usuario.email,
        'role': novo_usuario.role
    }
@app.post('/auth/login')
def login(
    dados: LoginEntrada,
    db: Session = Depends(get_db)
):
    usuario = db.scalars(
        select(models.UsuarioDB).where(
            models.UsuarioDB.email == dados.email
        )
    ).first()

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail= 'E-mail ou senha inválidos'
        )
    senha_correta = password_hash.verify(
        dados.senha,
        usuario.senha_hash
    )
    if not senha_correta:
        raise HTTPException(
            status_code=401,
            detail= 'E-mail ou senha incorreta'
        )
    token = criar_token(usuario)

    return {
        'access_token': token,
        'token_type': 'bearer',
    }






