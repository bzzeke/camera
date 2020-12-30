import io, os, time
import datetime as dt

from fastapi import APIRouter
from starlette.requests import Request
from hashlib import sha1

from api.models import ResponseModel, CredentialsModel
from api.auth import HTTPHeaderAuthentication, has_user, hash_credentials, get_user, set_user

router = APIRouter()

@router.post("/auth/signin")
def signin(request: Request, credentials: CredentialsModel):

    success = False
    if has_user():
        username, password = get_user()
        token = hash_credentials(credentials.username, sha1(credentials.password.encode('utf8')).hexdigest())
        if hash_credentials(username, password) == token:
            success = True

    return {
        "success": success,
        "results": [token] if success else None
    }

@router.post("/auth/signup")
def signup(request: Request, credentials: CredentialsModel):

    success = False
    if not has_user():
        set_user(credentials.username, credentials.password)
        token = hash_credentials(credentials.username, sha1(credentials.password.encode('utf8')).hexdigest())
        success = True

    return {
        "success": success,
        "results": [token] if success else None
    }

@router.get("/auth/is-new")
def is_new(request: Request):
    return {
        "success": not has_user()
    }
