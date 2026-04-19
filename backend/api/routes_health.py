from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.core.dependencies import get_db
from backend.logging_fastapi.logger_api import health_logger

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/health")
def health_check(
    db: Session = Depends(get_db)
    # redis=Depends(get_redis_client)
):
    health_logger.info("Health check initiated")

    db_status = "ok"
    redis_status = "ok"

    # 🔹 DB check
    try:
        db.execute(text("SELECT 1"))
        health_logger.info("Database connection successful")
    except Exception as e:
        health_logger.error(f"Database connection failed: {e}")
        db_status = "error"

    # 🔹 Redis check
    try:
        redis.ping()
        health_logger.info("Redis connection successful")
    except Exception as e:
        health_logger.error(f"Redis connection failed: {e}")
        redis_status = "error"


    if db_status == "ok" and redis_status == "ok":
        return {"status": "ok"}

    return {
        "status": "error",
        "details": {
            "database": db_status,
            "redis": redis_status
        }
    }
