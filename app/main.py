import time
import redis
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session
from sqlalchemy import text


from app.config import settings
from app.database import SessionLocal, get_db, get_redis, init_db
from app.metrics import (
    CACHE_HITS,
    CACHE_MISSES, 
    URL_LOOKUP_DURATION,
    URL_REDIRECTS,
    URLS_CREATED,
)

from app.models import URLItem
from app.schemas import AnalyticsResponse, ShortenRequest, ShortenResponse
from app.utils import encode_base62, is_valid_custom_alias


app = FastAPI(
    title="URL Shortener with Observability",
    version="1.0.0",
    description="A High-performance URL shortener with collision-free base62 encoding, Redis Caching, and Promethes/grafana observability",
)

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated = True,
    excluded_handlers=["/metrics", "/health"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

def increment_clicks(short_code: str):
    db = SessionLocal()
    try:
        item = (db.query(URLItem).filter(URLItem.short_code == short_code).first()
        )
        if item:
            item.clicks+=1
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health", tags=["System"])
def health_check(
    db: Session = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    try:
        db.execute(text("SELECT 1"))
        db.status = "connected"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error",
        )
    try:
        r.ping()
        redis_status = "connected"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"database": db.status, "redis": redis_status},
        )
    return {"status": "healthy", "database": "connected", "redis": "connected"}
@app.post(
    "/shorten",
    response_model = ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    tags = ["URL operations"],
)
def shorten_url(
    payload: ShortenRequest,
    db : Session = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    target_url = str(payload.url)
    if payload.custom_alias:
        if not is_valid_custom_alias(payload.custom_alias):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias must be 3-16 characters long(alphanumeric,dashes,underscores).",
            )
        existing = (
            db.query(URLItem)
            .filter(URLItem.short_code == payload.custom_alias)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Custom alias already in use.",
            )
        new_item = URLItem(original_url=target_url, short_code=payload.custom_alias)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        code = new_item.short_code
    else:
        new_item = URLItem(original_url=target_url)
        db.add(new_item)
        db.flush()
        code = encode_base62(new_item.id)
        new_item.short_code = code
        db.commit()
        db.refresh(new_item)
    try:
      r.set(f"url:{code}", target_url)
    except Exception:
      pass
    URLS_CREATED.inc()
    return ShortenResponse(
    short_code=new_item.short_code,
    short_url=f"{settings.base_url.rstrip('/')}/{new_item.short_code}",
    original_url=new_item.original_url,
    created_at=new_item.created_at,
)
@app.get("/{short_code}", tags=["URL operations"])
def redirect_to_url(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    start_time = time.perf_counter()
    cache_key = f"url:{short_code}"

    cached_url = None
    try:
        cached_url = r.get(cache_key)
    except Exception:
        pass
    if cached_url:
        CACHE_HITS.inc()
        URL_REDIRECTS.labels(status="success").inc()
        URL_LOOKUP_DURATION.observe(time.perf_counter() - start_time)
        background_tasks.add_task(increment_clicks, short_code)
        return RedirectResponse(
            url = cached_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
    CACHE_MISSES.inc()
    item = db.query(URLItem).filter(URLItem.short_code == short_code).first()
    lookup_time = time.perf_counter() - start_time
    URL_LOOKUP_DURATION.observe(lookup_time)

    if not item:
        URL_REDIRECTS.labels(status="not_found").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )
    try:
      r.set(cache_key, item.original_url)
    except Exception:
      pass
    item.clicks+=1
    db.commit()

    URL_REDIRECTS.labels(status="success").inc()
    return RedirectResponse(
        url = item.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
@app.get(
    "/analytics/{short_code}",
    response_model=AnalyticsResponse,
    tags=["URL operations"],
)
def get_analytics(short_code: str, db: Session = Depends(get_db)):
    item = db.query(URLItem).filter(URLItem.short_code == short_code).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found.",
        )
    return AnalyticsResponse(
        short_code=item.short_code,
        original_url=item.original_url,
        clicks=item.clicks,
        created_at=item.created_at,
    )