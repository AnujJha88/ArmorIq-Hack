---
description: RESTful API development with FastAPI including routing, validation, and authentication
---

# API Development with FastAPI

## Quick Start

// turbo
```powershell
pip install fastapi uvicorn pydantic python-multipart
```

## Project Structure
```
api/
├── main.py
├── routers/
│   ├── __init__.py
│   └── users.py
├── models/
│   └── schemas.py
├── services/
│   └── user_service.py
└── core/
    ├── config.py
    └── security.py
```

---

## Basic API Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="My API",
    version="1.0.0",
    description="API description"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

---

## Pydantic Models

```python
# models/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For ORM models
```

---

## CRUD Endpoints

```python
# routers/users.py
from fastapi import APIRouter, HTTPException, Depends, status

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
def list_users(skip: int = 0, limit: int = 100):
    return user_service.get_users(skip, limit)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    user = user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    return user_service.create(user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate):
    return user_service.update(user_id, user)

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int):
    user_service.delete(user_id)
```

---

## Authentication (JWT)

```python
# core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return get_user(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## Run Server

// turbo
```powershell
uvicorn main:app --reload --port 8000
```

Access docs at: `http://localhost:8000/docs`
