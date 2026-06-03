from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from database import get_db, init_db
from models import Customer, Staff, RefreshToken
from schemas import (
    CustomerRegisterRequest, StaffRegisterRequest,
    CustomerLoginRequest, StaffLoginRequest,
    TokenResponse, CustomerOut, StaffOut
)

app = FastAPI(title="Auth Service – Assignment 06", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Crypto ──────────────────────────────────────────────
SECRET_KEY = "learnmart-secret-key-2024-very-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 giờ

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Startup ─────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ════════════════════════════════════════════════════════
# HEALTH & METRICS  (Assignment 06)
# ════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "auth_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def auth_metrics(db: Session = Depends(get_db)):
    total_customers = db.query(Customer).count()
    total_staff = db.query(Staff).count()
    active_customers = db.query(Customer).filter(Customer.is_active == True).count()
    return {
        "service": "auth_service",
        "total_customers": total_customers,
        "active_customers": active_customers,
        "total_staff": total_staff,
    }


# ════════════════════════════════════════════════════════
# CUSTOMER ENDPOINTS
# ════════════════════════════════════════════════════════

@app.post("/register/customer", response_model=CustomerOut, status_code=201)
def register_customer(body: CustomerRegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký khách hàng mới"""
    if db.query(Customer).filter(Customer.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    customer = Customer(
        name=body.name,
        email=body.email,
        password=hash_password(body.password)
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@app.post("/login/customer", response_model=TokenResponse)
def login_customer(body: CustomerLoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập khách hàng, trả về JWT"""
    customer = db.query(Customer).filter(Customer.email == body.email).first()
    if not customer or not verify_password(body.password, customer.password):
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")

    token = create_access_token({
        "sub": str(customer.id),
        "user_type": "customer",
        "name": customer.name
    })
    return TokenResponse(
        access_token=token,
        user_type="customer",
        user_id=customer.id,
        name=customer.name
    )


@app.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    """[ADMIN] Danh sách tất cả khách hàng"""
    return db.query(Customer).all()


@app.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin khách hàng theo ID (dùng bởi các service khác)"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    return customer


# ════════════════════════════════════════════════════════
# STAFF ENDPOINTS
# ════════════════════════════════════════════════════════

@app.post("/register/staff", response_model=StaffOut, status_code=201)
def register_staff(body: StaffRegisterRequest, db: Session = Depends(get_db)):
    """Tạo tài khoản nhân viên"""
    if db.query(Staff).filter(Staff.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    staff = Staff(
        name=body.name,
        username=body.username,
        password=hash_password(body.password),
        role=body.role
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@app.post("/login/staff", response_model=TokenResponse)
def login_staff(body: StaffLoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập nhân viên, trả về JWT có role"""
    staff = db.query(Staff).filter(Staff.username == body.username).first()
    if not staff or not verify_password(body.password, staff.password):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
    if not staff.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")

    token = create_access_token({
        "sub": str(staff.id),
        "user_type": "staff",
        "role": staff.role,
        "name": staff.name
    })
    return TokenResponse(
        access_token=token,
        user_type="staff",
        user_id=staff.id,
        name=staff.name,
        role=staff.role
    )


@app.get("/staff", response_model=list[StaffOut])
def list_staff(db: Session = Depends(get_db)):
    """[ADMIN] Danh sách nhân viên"""
    return db.query(Staff).all()


@app.get("/staff/{staff_id}", response_model=StaffOut)
def get_staff(staff_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin nhân viên theo ID"""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return staff


# ════════════════════════════════════════════════════════
# TOKEN VERIFY (dùng bởi các service khác)
# ════════════════════════════════════════════════════════

@app.get("/verify-token")
def verify_token(token: str):
    """Xác minh JWT token – gọi bởi các microservice khác"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "user_id": int(payload["sub"]),
            "user_type": payload.get("user_type"),
            "role": payload.get("role"),
            "name": payload.get("name")
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")


@app.get("/me")
def get_me(token: str = None, authorization: str = None):
    """Lấy thông tin user hiện tại từ JWT (?token=... hoặc Authorization: Bearer ...)"""
    raw = token
    if not raw and authorization and authorization.startswith("Bearer "):
        raw = authorization[7:]
    if not raw:
        raise HTTPException(401, "Cần cung cấp token")
    try:
        payload = jwt.decode(raw, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "user_type": payload.get("user_type"),
            "role": payload.get("role"),
            "name": payload.get("name")
        }
    except Exception:
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")


@app.post("/change-password/customer")
def change_password_customer(customer_id: int, old_password: str, new_password: str, db: Session = Depends(get_db)):
    """Đổi mật khẩu khách hàng"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer or not verify_password(old_password, customer.password):
        raise HTTPException(400, "Mật khẩu cũ không đúng")
    customer.password = hash_password(new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công"}
