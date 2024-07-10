from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email : str 
    password: str

class UserDelete(BaseModel):
    email: str
    password: str

class SocialAuth(UserCreate):
    unique_key: str
    type: str
    profile_url: str

class UserPass(BaseModel):
    email: str
    password: str