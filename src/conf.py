import os
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv


CONNECTION_ID_LEN = 15
SQL_VERBOSE = True
ENCRYPTION_ALG = "HS256"
_ENGINE: None | Engine = None


def get_deepseek_api_key() -> str:
    return get_from_env("DEEPSEEK_API_KEY")


def get_jwt_secret() -> str:
    return get_from_env("JWT_SECRET")


def get_from_env(key: str) -> str:
    val = os.getenv(key)
    if val is None:
        raise EnvironmentError
    return val


def get_db_url() -> str:
    load_dotenv()
    user = get_from_env("POSTGRES_USER")
    pas = get_from_env("POSTGRES_PASSWORD")
    db = get_from_env("POSTGRES_DB")
    port = get_from_env("POSTGRES_PORT")
    host = get_from_env("POSTGRES_HOST")
    return f"postgresql://{user}:{pas}@{host}:{port}/{db}"


def get_engine(db_url: str) -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(db_url, echo=SQL_VERBOSE)
    return _ENGINE


def init_db(engine: Engine):
    SQLModel.metadata.create_all(engine)
