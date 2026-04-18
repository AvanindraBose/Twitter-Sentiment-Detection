from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.core.dependencies import get_db, get_redis_client, get_model

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    # DB check
    db.execute(text("SELECT 1"))

    # Redis check
    redis = get_redis_client()
    redis.ping()

    # Model check
    _ = get_model()

    return {
        "status": "ok"
    }
