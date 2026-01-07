from typing import Optional
import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Field, create_engine, Session, select
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Simple dev config (override via env or use docker-compose for postgres)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Medora Backend (dev)")

# --- Models ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False)
    hashed_password: str
    role: str  # 'elderly' or 'caregiver'
    linked_elderly_username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    linked_elderly_username: Optional[str] = None

# --- DB setup (dev simple sync) ---
engine = create_engine(DATABASE_URL, echo=False)
SQLModel.metadata.create_all(engine)

# --- Helpers ---
def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": subject, "role": role}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Routes ---
@app.post("/signup")
def signup(payload: UserCreate):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == payload.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = User(
            username=payload.username,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
            linked_elderly_username=payload.linked_elderly_username
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(subject=user.username, role=user.role)
        return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(subject=user.username, role=user.role)
        return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
