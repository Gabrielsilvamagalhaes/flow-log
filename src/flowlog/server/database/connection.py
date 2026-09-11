from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# Caminho absoluto a partir deste arquivo: o banco nao depende do diretorio
# de onde o servidor foi iniciado.
DATABASE_PATH = Path(__file__).resolve().parents[4] / "flowlog.db"

sqlite_url = f"sqlite:///{DATABASE_PATH.as_posix()}"
engine = create_engine(sqlite_url, echo=True)  # echo=True show sql commands in terminal


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("Created Database")


def get_session():
    with Session(engine) as session:
        yield session
