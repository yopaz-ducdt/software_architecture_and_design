from fastapi import Header, HTTPException, status
from jose import jwt, JWTError

SECRET_KEY = "learnmart-secret-key-2024-very-secure"
ALGORITHM = "HS256"


def decode_token(raw_token: str) -> dict:
    try:
        return jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
        ) from exc


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cần Bearer token để dùng AI chatbot",
        )
    token = authorization[7:]
    payload = decode_token(token)
    return {
        "user_id": int(payload.get("sub", 0) or 0),
        "user_type": payload.get("user_type", "customer"),
        "name": payload.get("name", "Khách hàng"),
        "role": payload.get("role", ""),
    }
