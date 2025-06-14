from pydantic import BaseModel, EmailStr


class SignInDto(BaseModel):
    email: EmailStr
    password: str


class SignUpDto(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
