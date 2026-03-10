from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Body
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from models import SessionLocal, Bookmark, Tag, BookmarkTag, User, SyncToken, engine
from ai_service import generate_summary, suggest_tags
import uuid
import datetime

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class BookmarkCreate(BaseModel):
    url: str = Field(..., max_length=2048, description="URL to bookmark")
    title: Optional[str] = None
    tags: Optional[List[str]] = None

class BookmarkResponse(BaseModel):
    id: str
    url: str
    title: str
    summary: Optional[str] = None
    suggestedTags: Optional[List[dict]] = None

class SummarizeRequest(BaseModel):
    url: str
    max_sentences: int = Field(2, ge=1, le=5)

class SuggestTagsRequest(BaseModel):
    url: str

class SyncTokenRequest(BaseModel):
    passphrase: str = Field(..., min_length=12)
    email: str

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_or_create_user(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/bookmarks", response_model=BookmarkResponse)
async def add_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    # Basic validation – ensure URL is not empty (Pydantic already does)    
    # Attempt to fetch AI summary and tags
    summary_res = await generate_summary({"url": payload.url, "max_sentences": 2})
    tags_res = await suggest_tags({"url": payload.url})

    summary_text = summary_res.get("summary")
    summary_conf = summary_res.get("confidence")
    suggested = tags_res.get("tags") or []

    # Persist bookmark
    bm = Bookmark(
        url=payload.url,
        title=payload.title or "",
        ai_summary=summary_text,
        ai_summary_confidence=summary_conf,
    )
    db.add(bm)
    db.commit()
    db.refresh(bm)

    # Persist tags and association
    for tag_info in suggested:
        tag_name = tag_info.get("tag")
        confidence = tag_info.get("confidence")
        if not tag_name:
            continue
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, is_ai_suggested=True)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        # Association
        assoc = BookmarkTag(bookmark_id=bm.id, tag_id=tag.id, confidence_score=confidence)
        db.add(assoc)
    db.commit()

    return BookmarkResponse(
        id=str(bm.id),
        url=bm.url,
        title=bm.title,
        summary=bm.ai_summary,
        suggestedTags=[{"tag": t.get("tag"), "confidence": t.get("confidence")} for t in suggested],
    )

@router.get("/bookmarks")
def list_bookmarks(tag: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Bookmark)
    if tag:
        query = query.join(BookmarkTag).join(Tag).filter(Tag.name == tag)
    bookmarks = query.all()
    return [
        {
            "id": str(b.id),
            "url": b.url,
            "title": b.title,
            "summary": b.ai_summary,
        }
        for b in bookmarks
    ]

@router.post("/ai/summarize")
async def ai_summarize(req: SummarizeRequest):
    res = await generate_summary({"url": req.url, "max_sentences": req.max_sentences})
    return res

@router.post("/ai/suggest-tags")
async def ai_suggest_tags(req: SuggestTagsRequest):
    res = await suggest_tags({"url": req.url})
    return res

@router.post("/sync/token")
def create_sync_token(payload: SyncTokenRequest, db: Session = Depends(get_db)):
    # In a real app the passphrase would be used client‑side; here we just create a token.
    user = get_or_create_user(db, payload.email)
    token_str = str(uuid.uuid4())
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = SyncToken(token=token_str, user_id=user.id, expires_at=expires)
    db.add(token)
    db.commit()
    db.refresh(token)
    return {"token": token_str, "expires_in": 86400, "salt": "placeholder-salt"}

@router.post("/sync/apply")
def apply_sync_token(token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    sync = db.query(SyncToken).filter(SyncToken.token == token).first()
    if not sync or sync.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    # For demo purposes, just return a placeholder.
    return {"note": "Sync logic not implemented in this demo"}
