from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import Update
from typing import Union



class RegisterUserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=15)

class LoginUserSchema(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=15)


class UpdateUserSchema(BaseModel):
    username: Union[str, None] = None
    email: Union[EmailStr, None] = None
    password: Union[str, None] = Field(default=None, min_length=8, max_length=15)



class Token(BaseModel):
    access_token: str
    token_type: str
    access_token_expires: str | None