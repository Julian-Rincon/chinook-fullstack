import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from .db import get_conn, init_app_tables
from . import services


def parse_cors_origins(value: str | None) -> list[str]:
    if not value:
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app = FastAPI(title="Chinook API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ALLOW_ORIGINS")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "chinook-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class PurchaseRequest(BaseModel):
    customer_id: int
    track_id: int
    quantity: int = Field(default=1, ge=1)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def to_public_user(row):
    return {
        "user_id": row["user_id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["role"],
        "is_active": row["is_active"],
    }


def get_user_by_email(conn, email: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, full_name, email, password_hash, role, is_active, created_at
            FROM app_user
            WHERE email = %(email)s
            """,
            {"email": email.lower().strip()},
        )
        return cur.fetchone()


def get_user_by_id(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, full_name, email, password_hash, role, is_active, created_at
            FROM app_user
            WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )
        return cur.fetchone()


def count_admins(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM app_user WHERE role = 'admin'")
        row = cur.fetchone()
        return int(row["total"])


def create_user_record(conn, full_name: str, email: str, password: str, role: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_user (full_name, email, password_hash, role, is_active)
            VALUES (%(full_name)s, %(email)s, %(password_hash)s, %(role)s, TRUE)
            RETURNING user_id, full_name, email, password_hash, role, is_active, created_at
            """,
            {
                "full_name": full_name.strip(),
                "email": email.lower().strip(),
                "password_hash": get_password_hash(password),
                "role": role,
            },
        )
        row = cur.fetchone()
    conn.commit()
    return row


def list_users(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, full_name, email, role, is_active, created_at
            FROM app_user
            ORDER BY user_id
            """
        )
        return cur.fetchall()


def get_current_user(token: str = Depends(oauth2_scheme), conn=Depends(get_conn)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    user = get_user_by_id(conn, user_id)
    if not user or not user["is_active"]:
        raise credentials_exception
    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


@app.on_event("startup")
def startup_event():
    init_app_tables()


@app.get("/health")
def health(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        cur.fetchone()
    return {"ok": True, "db": 1}


@app.post("/auth/bootstrap-admin")
def bootstrap_admin(payload: RegisterRequest, conn=Depends(get_conn)):
    if count_admins(conn) > 0:
        raise HTTPException(status_code=400, detail="Admin already exists")

    if get_user_by_email(conn, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user_record(conn, payload.full_name, payload.email, payload.password, "admin")
    token = create_access_token({"sub": str(user["user_id"]), "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": to_public_user(user),
    }


@app.post("/auth/register")
def register(payload: RegisterRequest, conn=Depends(get_conn)):
    if get_user_by_email(conn, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user_record(conn, payload.full_name, payload.email, payload.password, "user")
    return {
        "ok": True,
        "message": "User registered successfully",
        "user": to_public_user(user),
    }


@app.post("/auth/login")
def login(payload: LoginRequest, conn=Depends(get_conn)):
    user = get_user_by_email(conn, payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User inactive")

    token = create_access_token({"sub": str(user["user_id"]), "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": to_public_user(user),
    }


@app.get("/auth/me")
def me(current_user=Depends(get_current_user)):
    return to_public_user(current_user)


@app.get("/auth/admin/users")
def admin_users(current_user=Depends(require_admin), conn=Depends(get_conn)):
    rows = list_users(conn)
    return [dict(row) for row in rows]


@app.get("/search")
def search(q: str, limit: int = 20, conn=Depends(get_conn)):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="q is required")
    return services.search_tracks(conn, q.strip(), limit)


@app.get("/customer/{customer_id}")
def customer(customer_id: int, conn=Depends(get_conn)):
    data = services.get_customer_summary(conn, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return data


@app.post("/purchase")
def purchase(
    payload: PurchaseRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    try:
        return services.purchase_track(
            conn,
            payload.customer_id,
            payload.track_id,
            payload.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
