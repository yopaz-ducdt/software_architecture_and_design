from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db, init_db
from models import CustomerProfile, Address, Wishlist, WishlistItem, Newsletter, CustomerPreference
from schemas import (
    ProfileCreate, ProfileOut,
    AddressCreate, AddressOut,
    WishlistItemCreate, WishlistOut,
    NewsletterCreate, NewsletterOut,
    PreferenceCreate, PreferenceOut
)

app = FastAPI(title="Customer Service – Assignment 06", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ════════════════════════════════════════════════════════
# HEALTH & METRICS  (Assignment 06)
# ════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "customer_service", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
def customer_metrics(db: Session = Depends(get_db)):
    total_profiles = db.query(CustomerProfile).count()
    total_newsletters = db.query(Newsletter).filter(Newsletter.is_subscribed == True).count()
    return {
        "service": "customer_service",
        "total_profiles": total_profiles,
        "active_newsletter_subscriptions": total_newsletters,
    }


# ════════════════════════════════════════════════════════
# CUSTOMER PROFILE
# ════════════════════════════════════════════════════════
@app.post("/profile", response_model=ProfileOut, status_code=201)
def create_profile(body: ProfileCreate, db: Session = Depends(get_db)):
    if db.query(CustomerProfile).filter(CustomerProfile.customer_id == body.customer_id).first():
        raise HTTPException(400, "Hồ sơ đã tồn tại")
    profile = CustomerProfile(**body.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/profile/{customer_id}", response_model=ProfileOut)
def get_profile(customer_id: int, db: Session = Depends(get_db)):
    profile = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer_id).first()
    if not profile:
        raise HTTPException(404, "Không tìm thấy hồ sơ")
    return profile


@app.put("/profile/{customer_id}", response_model=ProfileOut)
def update_profile(customer_id: int, body: ProfileCreate, db: Session = Depends(get_db)):
    profile = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer_id).first()
    if not profile:
        raise HTTPException(404, "Không tìm thấy hồ sơ")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


# ════════════════════════════════════════════════════════
# ADDRESS
# ════════════════════════════════════════════════════════
@app.post("/addresses", response_model=AddressOut, status_code=201)
def add_address(body: AddressCreate, db: Session = Depends(get_db)):
    if body.is_default:
        db.query(Address).filter(
            Address.customer_profile_id == body.customer_profile_id,
            Address.is_default == True
        ).update({"is_default": False})
    address = Address(**body.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@app.get("/addresses/{customer_profile_id}", response_model=List[AddressOut])
def list_addresses(customer_profile_id: int, db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.customer_profile_id == customer_profile_id).all()


@app.delete("/addresses/{address_id}", status_code=204)
def delete_address(address_id: int, db: Session = Depends(get_db)):
    address = db.query(Address).filter(Address.id == address_id).first()
    if not address:
        raise HTTPException(404, "Không tìm thấy địa chỉ")
    db.delete(address)
    db.commit()


# ════════════════════════════════════════════════════════
# WISHLIST
# ════════════════════════════════════════════════════════
@app.get("/wishlist/{customer_id}", response_model=WishlistOut)
def get_wishlist(customer_id: int, db: Session = Depends(get_db)):
    wishlist = db.query(Wishlist).filter(Wishlist.customer_id == customer_id).first()
    if not wishlist:
        wishlist = Wishlist(customer_id=customer_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    return wishlist


@app.post("/wishlist/{customer_id}/toggle/{product_id}")
def toggle_wishlist(customer_id: int, product_id: int, db: Session = Depends(get_db)):
    """Thêm/Xóa sản phẩm khỏi wishlist (toggle)"""
    wishlist = db.query(Wishlist).filter(Wishlist.customer_id == customer_id).first()
    if not wishlist:
        wishlist = Wishlist(customer_id=customer_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)

    existing = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist.id,
        WishlistItem.book_id == product_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "removed", "product_id": product_id}
    else:
        item = WishlistItem(wishlist_id=wishlist.id, book_id=product_id)
        db.add(item)
        db.commit()
        return {"action": "added", "product_id": product_id}


# ════════════════════════════════════════════════════════
# NEWSLETTER
# ════════════════════════════════════════════════════════
@app.post("/newsletter/subscribe", response_model=NewsletterOut, status_code=201)
def subscribe(body: NewsletterCreate, db: Session = Depends(get_db)):
    existing = db.query(Newsletter).filter(Newsletter.email == body.email).first()
    if existing:
        existing.is_subscribed = True
        db.commit()
        return existing
    nl = Newsletter(**body.model_dump())
    db.add(nl)
    db.commit()
    db.refresh(nl)
    return nl


@app.delete("/newsletter/unsubscribe/{email}", status_code=204)
def unsubscribe(email: str, db: Session = Depends(get_db)):
    nl = db.query(Newsletter).filter(Newsletter.email == email).first()
    if nl:
        nl.is_subscribed = False
        db.commit()


# ════════════════════════════════════════════════════════
# CUSTOMER PREFERENCES
# ════════════════════════════════════════════════════════
@app.post("/preferences", response_model=PreferenceOut, status_code=201)
def create_preference(body: PreferenceCreate, db: Session = Depends(get_db)):
    existing = db.query(CustomerPreference).filter(
        CustomerPreference.customer_id == body.customer_id
    ).first()
    if existing:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    pref = CustomerPreference(**body.model_dump())
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


@app.get("/preferences/{customer_id}", response_model=PreferenceOut)
def get_preferences(customer_id: int, db: Session = Depends(get_db)):
    pref = db.query(CustomerPreference).filter(CustomerPreference.customer_id == customer_id).first()
    if not pref:
        raise HTTPException(404, "Chưa có sở thích nào được lưu")
    return pref
