from sqlalchemy import Engine
from sqlmodel import Session, select
from models import User


def get_user_by_id(engine: Engine, user_id: int) -> User | None:
    found_user: User | None = None
    with Session(engine) as session:
        statement = select(User).where(User.id == user_id)
        res = session.exec(statement)
        found_user = res.first()
    return found_user


def get_user_by_email(engine: Engine, email: str) -> User | None:
    found_user: User | None = None
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        res = session.exec(statement)
        found_user = res.first()
    return found_user


def get_user_by_username(engine: Engine, username: str) -> User | None:
    found_user: User | None = None
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        res = session.exec(statement)
        found_user = res.first()
    return found_user
