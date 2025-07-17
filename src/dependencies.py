from dataclasses import dataclass

from fastapi import HTTPException, status, Depends
import jwt
from fastapi.security import OAuth2PasswordBearer

@dataclass
class UserClaims:
    id: str
    access_level: str
    payload: dict



SECRET_KEY = "secret"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def decode_jwt_token(token:str = Depends(oauth2_scheme)) -> UserClaims:
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        access_level = payload.get("access_level")
        msg = payload.get("payload")
        if not user_id or not access_level:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")
        return UserClaims(user_id, access_level, msg)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")