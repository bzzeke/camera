import io, os, time
import datetime as dt
import jdb

from fastapi import Header
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from hashlib import sha1

from adapters.fastapi import APIException

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
