import io, os, time
import datetime as dt

from fastapi import Header
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from hashlib import sha1

from adapters.fastapi import APIException
from models.config import config

class HTTPHeaderAuthentication:

    async def __call__(self, request: Request, authorization: str = Header(None)):
        user = self.locate_user(id=authorization)
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
    if config.user.username != "":
        return True

    return False

def set_user(username, password):
    config.user.username = username
    config.user.password = sha1(password.encode('utf8')).hexdigest()
    config.save()

def get_user():
    return (config.user.username, config.user.password)
