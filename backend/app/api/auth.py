from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext

from app.db_utils import get_user_by_email, create_user
from app.core.security import create_access_token

router = APIRouter()

# support bcrypt and pbkdf2_sha256 for compatibility across environments
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], default="pbkdf2_sha256", deprecated="auto")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: str = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(req: RegisterRequest):
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")
    password_hash = pwd_context.hash(req.password)
    user_id = create_user(req.email, password_hash, req.full_name, req.phone, is_admin=False)
    token = create_access_token({"sub": req.email, "user_id": user_id})
    return {"user": {"id": user_id, "email": req.email, "full_name": req.full_name}, "token": token}


@router.post("/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["email"], "user_id": user["id"], "is_admin": user["is_admin"]})
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "is_admin": user["is_admin"]}}