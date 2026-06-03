import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import Base, StaffDepartment, StaffMember
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/staff_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_db(retries: int = 30, delay: int = 2):
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            import time
            time.sleep(delay)
    if last_error:
        raise last_error


app = FastAPI(title="Staff Service – Assignment 06", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "staff_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def staff_metrics(db: Session = Depends(get_db)):
    total_members = db.query(StaffMember).count()
    active_members = db.query(StaffMember).filter(StaffMember.is_active == True).count()
    return {
        "service": "staff_service",
        "total_members": total_members,
        "active_members": active_members,
    }



# ── Schemas ──────────────────────────────────────────────
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    class Config: from_attributes = True


class StaffMemberCreate(BaseModel):
    staff_id: int
    department_id: Optional[int] = None
    phone: Optional[str] = None
    salary: Optional[int] = None


class StaffMemberOut(BaseModel):
    id: int
    staff_id: int
    department_id: Optional[int]
    phone: Optional[str]
    salary: Optional[int]
    hire_date: datetime
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════
# DEPARTMENT
# ════════════════════════════════════════════════════════
@app.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(body: DepartmentCreate, db: Session = Depends(get_db)):
    dept = StaffDepartment(**body.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@app.get("/departments", response_model=List[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return db.query(StaffDepartment).all()


# ════════════════════════════════════════════════════════
# STAFF MEMBER PROFILE
# ════════════════════════════════════════════════════════
@app.post("/members", response_model=StaffMemberOut, status_code=201)
def create_member(body: StaffMemberCreate, db: Session = Depends(get_db)):
    if db.query(StaffMember).filter(StaffMember.staff_id == body.staff_id).first():
        raise HTTPException(400, "Thành viên đã tồn tại")
    member = StaffMember(**body.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.get("/members", response_model=List[StaffMemberOut])
def list_members(db: Session = Depends(get_db)):
    return db.query(StaffMember).all()


@app.get("/members/{staff_id}", response_model=StaffMemberOut)
def get_member(staff_id: int, db: Session = Depends(get_db)):
    member = db.query(StaffMember).filter(StaffMember.staff_id == staff_id).first()
    if not member:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return member


@app.patch("/members/{staff_id}/deactivate")
def deactivate_member(staff_id: int, db: Session = Depends(get_db)):
    member = db.query(StaffMember).filter(StaffMember.staff_id == staff_id).first()
    if not member:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    member.is_active = False
    db.commit()
    return {"message": f"Đã vô hiệu hóa nhân viên {staff_id}"}
