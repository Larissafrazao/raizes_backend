# API Raízes do Nordeste

Projeto Back-End desenvolvido para gerenciamento de uma rede de lanchonetes, contemplando produtos, unidades, estoque por unidade, pedidos multicanal, pagamento mock e autenticação JWT.

## Tecnologias utilizadas

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- PyJWT
- pwdlib
- Uvicorn

## Pré-requisitos

- Python instalado
- PostgreSQL instalado
- Git

## Instalação

Clone o repositório:

git clone https://github.com/Larissafrazao/raizes_backend

Entre na pasta:

cd raizes_backend

Instale as dependências:

pip install -r requirements.txt

## Variáveis de ambiente

Crie um arquivo `.env` baseado no `.env.example`.

Exemplo:

DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/raizes_nordeste
JWT_SECRET_KEY=sua_chave_secreta

## Banco de dados

Criar no PostgreSQL um banco chamado:

raizes_nordeste

As tabelas utilizadas pela aplicação são criadas por meio do SQLAlchemy.

## Executando a API

uvicorn main:app --reload

## Swagger

Após iniciar a aplicação:

http://127.0.0.1:8000/docs

## Autenticação

1. Cadastrar um usuário em POST /usuarios
2. Realizar login em POST /auth/login
3. Copiar o access_token
4. Utilizar o botão Authorize do Swagger

## Fluxo principal

Pedido
→ validação de estoque
→ baixa de estoque
→ pagamento mock
→ atualização do status

## Testes

Os testes podem ser realizados pelo Swagger ou pela coleção Postman disponível na pasta /postman.

## Observações

Funcionalidades como fidelização, promoções e auditoria persistente são consideradas evoluções futuras do MVP.