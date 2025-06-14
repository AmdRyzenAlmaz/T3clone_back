from datetime import datetime, timedelta, timezone
import random
import string
import jwt

from conf import CONNECTION_ID_LEN, get_jwt_secret


def gen_connection_id() -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(CONNECTION_ID_LEN)
    )


def gen_jwt(user_id: int, days_to_live: float) -> str:
    token = jwt.encode(
        {
            "sub": user_id,
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=days_to_live),
        },
        get_jwt_secret(),
    )
    return token
