# imports 
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body, Query
from fastapi import Depends, APIRouter, HTTPException, status, Request, Response
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import asyncio
import json
from typing import List, Dict, Any
from typing import AsyncIterable
import jwt
import secrets
import string
import random
from contextlib import asynccontextmanager
from routes.user import user_router
from routes.talk import chat_router


#-------------------------------------------------------- End of Imports --------------------------------------------------------#
origins = ['*']

app = FastAPI(
    title="Neuron Service Tech",
    description="Neuron Service Tech Application backend for customized AI Agents"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=origins,
    allow_headers=origins,
)

app.include_router(user_router, prefix="/user")
app.include_router(chat_router)