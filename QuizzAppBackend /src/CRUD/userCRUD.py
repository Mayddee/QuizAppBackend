import datetime
from datetime import timedelta, datetime, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, Depends, APIRouter, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.DatabaseManager.queries import get_session
from src.Schemas.QuizShema import QuizRead
from src.Schemas.UserSchema import RegisterUserSchema, LoginUserSchema, Token
from src.Models.models import User, Quiz
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT SETTINGS
SECRET_KEY = "MY_SUPER_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
COOKIE_NAME = "access_token"




def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)




@router.patch("/update")
async def update_user():
    ...



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user_from_cookie(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    return payload.get("sub")

async def get_current_user_id_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_session)
) -> int:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user.id

@router.post("/register")
async def register_user(data: RegisterUserSchema, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(data.password)
    user = User(username=data.username, email=data.email, hashed_password=hashed_password)
    session.add(user)
    await session.commit()
    return {"message": "User registered"}

@router.post("/login", response_model=Token)
async def login_user(
    data: LoginUserSchema,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.username})
    expire_duration = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=3600,
        samesite="lax",
        secure=False  # True for production with HTTPS
    )
    return Token(access_token=token, token_type="bearer", access_token_expires=str(expire_duration))


@router.get("/me")
async def read_me(current_user: str = Depends(get_current_user_from_cookie)):
    return {"user": current_user}


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Logged out"}

@router.get("/quiz/my-quizzes", response_model=list[QuizRead])
async def get_my_quizzes(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id_from_cookie)
):
    result = await session.execute(select(Quiz).where(Quiz.creator_id == user_id))
    return result.scalars().all()