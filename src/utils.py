from datetime import datetime, timedelta, timezone
from threading import Lock
import random
import string
from typing import Any, Dict
import jwt

from conf import CONNECTION_ID_LEN, ENCRYPTION_ALG, get_jwt_secret


def gen_connection_id() -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(CONNECTION_ID_LEN)
    )


def gen_jwt(user_id: int, days_to_live: float) -> str:
    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=days_to_live),
        },
        get_jwt_secret(),
        algorithm=ENCRYPTION_ALG,
    )
    return token


def decode_jwt(jw_token: str) -> Dict[str, Any] | None:
    try:
        claims = jwt.decode(
            jw_token,
            get_jwt_secret(),
            options={"require": ["exp"]},
            verify=True,
            algorithms=ENCRYPTION_ALG,
        )
    except Exception as e:
        print(e)
        return None
    return claims


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
