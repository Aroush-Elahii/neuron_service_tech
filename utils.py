from datetime import datetime, timedelta
from database.models.models import User
from database.config.connection import *
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, APIRouter, HTTPException, status, Request, Response, Security
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from typing import Optional, Dict, Any
import os
import random 
import string
import re

SECRET_KEY = "scnkjsdbjch32737rt387r6cjkjcb78887dscjh29ue092ue8932"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALGORITHM = "HS256"

# create user token 
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(weeks=26)  # 26 weeks = 6 months
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# verify user token 
def verify_token(token: str, credentials_exception):
    if token is None:
        raise credentials_exception
    else:
        try:
            token = token[len("Bearer "):] if token.startswith("Bearer ") else token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            # You can also add more checks here (e.g., token expiration)
            return payload
        except JWTError:
            print("INSIDE THE EXCEPT BLOCK:\n")
            raise credentials_exception

# authenticat current user      
def authenticate_user(email: str, password: str):
    user = collection_users.find_one({"$or": [{"email": email}], "password": password, "is_deleted": False})
    return user


# get user info 
async def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token, credentials_exception)
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = collection_users.find_one({"username": username}, {"_id": 1, "username": 1, "email": 1})

    if user:
        user_dict = {
            "success": True,
            "message": "User granted successfully!",
            "user": user,
            "user_id": str(user["_id"]),
            "token": token
        }
        return user_dict
    else:
        return None
    
def generate_password(length=12):
    # Define character sets
    letters = string.ascii_letters
    digits = string.digits
    punctuation = string.punctuation

    # Combine character sets
    all_chars = letters + digits + punctuation

    # Generate password
    password = ''.join(random.choice(all_chars) for _ in range(length))

    return password

