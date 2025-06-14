from fastapi import APIRouter, HTTPException, Request
import fastapi
import bcrypt
from sqlmodel import Session, select

from auth import dto
import models
import utils

router = APIRouter()


@router.post("/sign-in")
async def sign_in(request: Request, user: dto.SignInDto):
    engine = request.app.state.engine
    found_user: models.User | None = None
    with Session(engine) as session:
        statement = select(models.User).where(models.User.email == user.email)
        res = session.exec(statement)
        found_user = res.first()

    if found_user is None or found_user.id is None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail={"success": False, "data": "user not found"},
        )

    if not bcrypt.checkpw(user.password.encode(), found_user.password.encode()):
        raise HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail={"success": False, "data": "password incorrect"},
        )
    access_token = utils.gen_jwt(found_user.id, 1.0)
    refresh_token = utils.gen_jwt(found_user.id, 7.0)
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/sign-up")
async def sign_up(request: Request, user: dto.SignUpDto):
    engine = request.app.state.engine
    found_user: models.User | None = None
    with Session(engine) as session:
        statement = select(models.User).where(
            models.User.email == user.email or models.User.username == user.username
        )
        res = session.exec(statement)
        found_user = res.first()

    if found_user is not None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "data": "user with same email or username already exists",
            },
        )
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "data": "password and do not match",
            },
        )

    password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    insert_user = models.User(
        username=user.username, email=user.email, password=password
    )
    inserted_user: models.User | None = None
    with Session(engine) as session:
        session.add(insert_user)
        session.commit()
        statement = select(models.User).where(models.User.email == user.email)
        res = session.exec(statement)
        inserted_user = res.first()

    if inserted_user is None or inserted_user.id is None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal server error",
        )

    access_token = utils.gen_jwt(inserted_user.id, 1.0)
    refresh_token = utils.gen_jwt(inserted_user.id, 7.0)
    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
