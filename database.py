import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
class Base(DeclarativeBase):
    pass

# from sqlalchemy import text
#
#
# try:
#     with engine.connect() as conexao:
#         resultado = conexao.execute(text("SELECT 1"))
#
#         print("Conexão com PostgreSQL realizada com sucesso!")
#         print(resultado.scalar())
#
# except Exception as erro:
#     print("Erro ao conectar:")
#     print(erro)