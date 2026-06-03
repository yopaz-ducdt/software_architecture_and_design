"""
API Gateway – Assignment 06
============================
Thay thế nginx thuần bằng FastAPI proxy thông minh với:
  - JWT validation & RBAC (role-based access control)
  - Request logging
  - In-memory rate limiting (per IP)
  - Reverse proxy tới các upstream services qua httpx
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
import httpx
from jose import jwt, JWTError
from datetime import datetime, timedelta
from collections import defaultdict
import time
import logging

# ── Config ────────────────────────────────────────────
SECRET_KEY = "learnmart-secret-key-2024-very-secure"
ALGORITHM  = "HS256"

# Rate limiting: tối đa MAX_REQUESTS request trong WINDOW_SECONDS giây mỗi IP
MAX_REQUESTS   = 60
WINDOW_SECONDS = 60

# Mapping prefix → upstream URL  (service name dùng được trong Docker network)
UPSTREAM = {
    "/auth/":          "http://auth_service:8001",
    "/products/":      "http://product_service:8002",
    "/books/":         "http://product_service:8002",
    "/orders/":        "http://order_service:8003",
    "/customers/":     "http://customer_service:8004",
    "/staff/":         "http://staff_service:8005",
    "/marketing/":     "http://marketing_service:8006",
    "/inventory/":     "http://inventory_service:8007",
    "/content/":       "http://content_service:8008",
    "/interaction/":   "http://interaction_service:8009",
    "/analytics/":     "http://analytics_service:8010",
    "/notifications/": "http://notification_service:8011",
    "/behavior/":      "http://behavior_service:8013",
    "/ai/":            "http://ai_chat_service:8012",
}

# Các path KHÔNG cần JWT (public endpoints)
PUBLIC_PATHS = {
    "/auth/login/customer",
    "/auth/login/staff",
    "/auth/register/customer",
    "/auth/register/staff",
    "/health",
    "/",
}

# Các path chỉ dành cho staff
STAFF_ONLY_PREFIXES = [
    "/staff/",
    "/inventory/",
    "/analytics/",
    "/marketing/",
]

# ── Logging setup ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GATEWAY] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api_gateway")

# ── Rate-limit store ─────────────────────────────────
# { ip: [(timestamp, count), ...] }  – sliding window
_rate_store: dict[str, list] = defaultdict(list)

def check_rate_limit(ip: str) -> bool:
    """Return True nếu request được phép (chưa vượt giới hạn)."""
    now = time.time()
    window_start = now - WINDOW_SECONDS
    # Loại bỏ các entry cũ
    _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]
    if len(_rate_store[ip]) >= MAX_REQUESTS:
        return False
    _rate_store[ip].append(now)
    return True

# ── JWT helper ────────────────────────────────────────
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ── App ───────────────────────────────────────────────
app = FastAPI(title="API Gateway – Assignment 06", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Metrics counter (in-memory) ───────────────────────
_metrics = {
    "total_requests": 0,
    "rejected_rate_limit": 0,
    "rejected_auth": 0,
    "rejected_forbidden": 0,
    "forwarded": 0,
    "started_at": datetime.utcnow().isoformat(),
}

# ── Health / Metrics endpoints ────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "api_gateway", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def metrics():
    return _metrics


@app.get("/")
def root():
    return {
        "service": "LearnMart API Gateway (Assignment 06)",
        "version": "2.0.0",
        "features": ["JWT RBAC", "Rate Limiting", "Request Logging", "Saga-ready"],
        "routes": list(UPSTREAM.keys()),
    }


# ── Main catch-all proxy ──────────────────────────────
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def gateway(full_path: str, request: Request):
    _metrics["total_requests"] += 1
    path = "/" + full_path
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    start = time.time()

    # ── 1. Rate limiting ───────────────────────────────
    if not check_rate_limit(client_ip):
        _metrics["rejected_rate_limit"] += 1
        logger.warning(f"RATE LIMIT {client_ip} {method} {path}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quá nhiều yêu cầu. Giới hạn: {MAX_REQUESTS} request/{WINDOW_SECONDS}s",
        )

    # ── 2. JWT Authentication ──────────────────────────
    user_payload: dict | None = None
    is_public = path in PUBLIC_PATHS or any(path.startswith(p) for p in ["/auth/login", "/auth/register"])

    if not is_public:
        auth_header = request.headers.get("Authorization", "")
        token_param = request.query_params.get("token")
        raw_token = None
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:]
        elif token_param:
            raw_token = token_param

        if not raw_token:
            _metrics["rejected_auth"] += 1
            logger.warning(f"NO TOKEN  {client_ip} {method} {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Yêu cầu xác thực. Vui lòng cung cấp JWT token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_payload = decode_token(raw_token)

    # ── 3. RBAC – kiểm tra quyền ──────────────────────
    if user_payload:
        user_type = user_payload.get("user_type", "")
        role      = user_payload.get("role", "")
        # Các path staff-only: chỉ cho user_type == "staff"
        if any(path.startswith(p) for p in STAFF_ONLY_PREFIXES):
            if user_type != "staff":
                _metrics["rejected_forbidden"] += 1
                logger.warning(f"FORBIDDEN {client_ip} {method} {path} user_type={user_type}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền truy cập endpoint này (chỉ dành cho nhân viên)",
                )

    # ── 4. Route matching ──────────────────────────────
    upstream_base = None
    upstream_path = path
    for prefix, base in UPSTREAM.items():
        if path.startswith(prefix):
            upstream_base = base
            # Strip prefix, keep rest e.g. /books/1 → /1
            upstream_path = path[len(prefix)-1:]   # giữ leading /
            break

    if not upstream_base:
        raise HTTPException(status_code=404, detail=f"Route không tồn tại: {path}")

    # ── 5. Forward request ─────────────────────────────
    target_url = upstream_base + upstream_path
    qs = str(request.url.query)
    if qs:
        target_url += "?" + qs

    # Forward headers (loại bỏ hop-by-hop headers)
    excluded = {"host", "content-length", "transfer-encoding", "connection"}
    fwd_headers = {k: v for k, v in request.headers.items() if k.lower() not in excluded}

    # Inject user info ở header nếu đã xác thực
    if user_payload:
        fwd_headers["X-User-Id"]   = str(user_payload.get("sub", ""))
        fwd_headers["X-User-Type"] = user_payload.get("user_type", "")
        fwd_headers["X-User-Role"] = user_payload.get("role", "")
        fwd_headers["X-User-Name"] = user_payload.get("name", "")

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=method,
                url=target_url,
                headers=fwd_headers,
                content=body,
            )
        elapsed = round((time.time() - start) * 1000, 1)
        logger.info(f"{method} {path} → {target_url} [{resp.status_code}] {elapsed}ms ip={client_ip}")
        _metrics["forwarded"] += 1

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.headers.get("content-type"),
        )
    except httpx.ConnectError:
        logger.error(f"CONNECT ERROR → {target_url}")
        raise HTTPException(status_code=502, detail=f"Service không khả dụng: {upstream_base}")
    except httpx.TimeoutException:
        logger.error(f"TIMEOUT → {target_url}")
        raise HTTPException(status_code=504, detail="Service timeout")
