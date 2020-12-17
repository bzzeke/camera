import io, os, time
import datetime as dt
import uuid
import jdb

from fastapi import APIRouter, Header
from starlette.requests import Request
from typing import Set, List
from starlette.status import HTTP_403_FORBIDDEN
from pydantic import BaseModel, Schema
from hashlib import sha1

from util import log
from api.models import ResponseModel,CredentialsModel
from adapters.fastapi import APIException

router = APIRouter()

@router.post("/signin", response_model=ResponseModel)
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

@router.post("/signup", response_model=ResponseModel)
def signup(request: Request, credentials: CredentialsModel):

    success = False
    if not has_user():
        set_user(credentials.username, credentials.password)
        success = True

    return {
        "success": success
    }

class HTTPHeaderAuthentication:

    async def __call__(self, request: Request, authentication: str = Header(None)):
        user = self.locate_user(id=authentication)
        if not user:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        return user

    def locate_user(self, id: str):
        if has_user():
            username, password = get_user()
            user_hash = hash_credentials(username, password)
            if user_hash == id:
                return True

        return False


def hash_credentials(username, password):
    return sha1("{}{}".format(username, password).encode('utf8')).hexdigest()

def has_user():
    db = jdb.load("{}/data/user.json".format(os.environ["STORAGE_PATH"]), True)
    if db.get("username"):
        return True

    return False

def set_user(username, password):
    db = jdb.load("{}/data/user.json".format(os.environ["STORAGE_PATH"]), True)
    db.set("username", username)
    db.set("password", sha1(password.encode('utf8')).hexdigest())

def get_user():
    db = jdb.load("{}/data/user.json".format(os.environ["STORAGE_PATH"]), True)
    return (db.get("username"), db.get("password"))
