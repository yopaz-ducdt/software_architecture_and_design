import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Duyanh090%40@mysql:3306/content_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
app = FastAPI(title="Content Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════ MODELS ════════════════════════════════════════

# MODEL 1: Collection – Bộ sưu tập / danh mục tuyển chọn
class Collection(Base):
    __tablename__ = "collection"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)
    # Books in collection stored as comma-separated IDs (simple demo approach)
    book_ids = Column(Text, nullable=True)


# MODEL 2: BookAward – Giải thưởng sách
class BookAward(Base):
    __tablename__ = "book_award"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False)   # FK to book_service
    award_name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=True)
    category = Column(String(255), nullable=True)


# MODEL 3: Banner – Banner/quảng cáo trang chủ
class Banner(Base):
    __tablename__ = "banner"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    link_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)


# MODEL 4: BlogPost – Bài viết blog / tin tức (thêm mới)
class BlogPost(Base):
    """Bài viết blog về sách, tác giả, reviews (nội dung editorial)"""
    __tablename__ = "blog_post"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    body = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=True)    # content writer, not book author
    cover_image = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(String(255), nullable=True)            # comma-separated tags


# ══ Schemas ════════════════════════════════════════════
class CollectionCreate(BaseModel):
    name: str; slug: str; description: Optional[str] = None
    cover_image: Optional[str] = None; book_ids: Optional[str] = None


class CollectionOut(BaseModel):
    id: int; name: str; slug: str; description: Optional[str]
    active: bool; book_ids: Optional[str]
    class Config: from_attributes = True


class AwardCreate(BaseModel):
    book_id: int; award_name: str; year: Optional[int] = None; category: Optional[str] = None


class AwardOut(BaseModel):
    id: int; book_id: int; award_name: str; year: Optional[int]; category: Optional[str]
    class Config: from_attributes = True


class BannerCreate(BaseModel):
    title: str; subtitle: Optional[str] = None; image_url: Optional[str] = None
    link_url: Optional[str] = None; order: int = 0


class BannerOut(BaseModel):
    id: int; title: str; subtitle: Optional[str]; image_url: Optional[str]
    link_url: Optional[str]; is_active: bool; order: int
    class Config: from_attributes = True


class BlogPostCreate(BaseModel):
    title: str; slug: str; body: str
    author_name: Optional[str] = None; cover_image: Optional[str] = None
    tags: Optional[str] = None


class BlogPostOut(BaseModel):
    id: int; title: str; slug: str; author_name: Optional[str]
    is_published: bool; published_at: Optional[datetime]; tags: Optional[str]
    class Config: from_attributes = True


# ══ Startup ════════════════════════════════════════════
def wait_for_db(retries: int = 30, delay: int = 2):
    import time
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay)
    if last_error:
        raise last_error

@app.on_event("startup")
def startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "content_service", "timestamp": datetime.utcnow().isoformat()}


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# ════════ ROUTES ════════════════════════════════════════

@app.post("/collections", response_model=CollectionOut, status_code=201)
def create_collection(body: CollectionCreate, db: Session = Depends(get_db)):
    c = Collection(**body.model_dump()); db.add(c); db.commit(); db.refresh(c); return c


@app.get("/collections", response_model=List[CollectionOut])
def list_collections(db: Session = Depends(get_db)):
    return db.query(Collection).filter(Collection.active == True).all()


@app.get("/collections/{slug}", response_model=CollectionOut)
def get_collection(slug: str, db: Session = Depends(get_db)):
    c = db.query(Collection).filter(Collection.slug == slug).first()
    if not c: raise HTTPException(404, "Không tìm thấy collection")
    return c


@app.post("/awards", response_model=AwardOut, status_code=201)
def create_award(body: AwardCreate, db: Session = Depends(get_db)):
    a = BookAward(**body.model_dump()); db.add(a); db.commit(); db.refresh(a); return a


@app.get("/awards", response_model=List[AwardOut])
def list_awards(db: Session = Depends(get_db)):
    return db.query(BookAward).order_by(BookAward.year.desc()).all()


@app.post("/banners", response_model=BannerOut, status_code=201)
def create_banner(body: BannerCreate, db: Session = Depends(get_db)):
    b = Banner(**body.model_dump()); db.add(b); db.commit(); db.refresh(b); return b


@app.get("/banners", response_model=List[BannerOut])
def list_banners(db: Session = Depends(get_db)):
    return db.query(Banner).filter(Banner.is_active == True).order_by(Banner.order).all()


@app.post("/blog", response_model=BlogPostOut, status_code=201)
def create_post(body: BlogPostCreate, db: Session = Depends(get_db)):
    post = BlogPost(**body.model_dump()); db.add(post); db.commit(); db.refresh(post); return post


@app.get("/blog", response_model=List[BlogPostOut])
def list_posts(db: Session = Depends(get_db)):
    return db.query(BlogPost).filter(BlogPost.is_published == True).order_by(BlogPost.published_at.desc()).all()


@app.patch("/blog/{post_id}/publish")
def publish_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post: raise HTTPException(404, "Không tìm thấy bài viết")
    post.is_published = True; post.published_at = datetime.utcnow()
    db.commit()
    return {"post_id": post_id, "published": True}
