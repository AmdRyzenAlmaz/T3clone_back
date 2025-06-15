from fastapi import APIRouter, HTTPException, Request
import fastapi
import bcrypt
from sqlmodel import Session, select

from auth import dto, repository
import models
import utils

router = APIRouter()


@router.post("/sign-in")
async def sign_in(request: Request, user: dto.SignInDto):
    engine = request.app.state.engine
    found_user = repository.get_user_by_email(engine, user.email)

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
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }


@router.post("/sign-up")
async def sign_up(request: Request, user: dto.SignUpDto):
    engine = request.app.state.engine
    found_user_by_email = repository.get_user_by_email(engine, user.email)
    found_user_by_username = repository.get_user_by_username(engine, user.username)

    if found_user_by_email is not None or found_user_by_username is None:
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
    with Session(engine) as session:
        session.add(insert_user)
        session.commit()

    inserted_user = repository.get_user_by_email(engine, user.email)
    if inserted_user is None or inserted_user.id is None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal server error",
        )

    access_token = utils.gen_jwt(inserted_user.id, 1.0)
    refresh_token = utils.gen_jwt(inserted_user.id, 7.0)
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }


@router.post("/refresh")
async def refresh(request: Request, refresh_dto: dto.RefreshDto):
    engine = request.app.state.engine
    refresh_claims = utils.decode_jwt(refresh_dto.refresh_token)
    if refresh_claims is None or refresh_claims.get("sub") is None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "data": "invalid token"},
        )

    found_user = repository.get_user_by_id(engine, int(refresh_claims.get("sub", 0)))

    if found_user is None or found_user.id is None:
        raise HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail={"success": False, "data": "user not found"},
        )
    access_token = utils.gen_jwt(found_user.id, 1.0)
    refresh_token = utils.gen_jwt(found_user.id, 7.0)
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }
