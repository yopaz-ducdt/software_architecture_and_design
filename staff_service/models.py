from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ════════════════════════════════════════════════════════
# MODEL 1: StaffDepartment – Phòng ban
# (thêm mới để đủ 50 model toàn hệ thống)
# ════════════════════════════════════════════════════════
class StaffDepartment(Base):
    """Phòng ban / bộ phận trong cửa hàng"""
    __tablename__ = "staff_department"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)   # e.g., "Warehouse", "Customer Support"
    description = Column(Text, nullable=True)

    members = relationship("StaffMember", back_populates="department")


# ════════════════════════════════════════════════════════
# MODEL 2: StaffMember – Thông tin mở rộng nhân viên
# ════════════════════════════════════════════════════════
class StaffMember(Base):
    """Thông tin chi tiết nhân viên (auth_service giữ login info)"""
    __tablename__ = "staff_member"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, unique=True, nullable=False)   # FK to auth_service.staff
    department_id = Column(Integer, ForeignKey("staff_department.id"), nullable=True)
    phone = Column(String(255), nullable=True)
    hire_date = Column(DateTime, default=datetime.utcnow)
    salary = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    department = relationship("StaffDepartment", back_populates="members")
