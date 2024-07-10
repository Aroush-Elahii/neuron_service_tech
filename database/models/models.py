from pydantic import BaseModel 
from datetime import datetime

class User(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    otp: str
    is_verified: bool = True
    is_deleted: bool = False
    added_on: datetime = datetime.now()
    updated_on: datetime = datetime.now()

## for social_auth 
# class User(BaseModel):
#     first_name: str
#     last_name: str
#     email: str
#     username: str
#     password: str
#     otp: str
#     unique_key: str
#     type: str
#     is_verified: bool = True
#     is_deleted: bool = False
#     added_on: datetime = datetime.now()
#     updated_on: datetime = datetime.now()