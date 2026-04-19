import logging
from fastapi import HTTPException,Request,status,Depends
from backend.core.dependencies import get_redis_client , get_refresh_user_id , get_current_user
import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from redis.exceptions import RedisError
from backend.logging_fastapi.logger_api import prediction_logger,auth_logger

load_dotenv()
logger = logging.getLogger(__name__)
LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", 5))
LOGIN_RATE_WINDOW = int(os.getenv("LOGIN_RATE_WINDOW", 60))

REFRESH_RATE_LIMIT = int(os.getenv("REFRESH_RATE_LIMIT", 10))
REFRESH_RATE_WINDOW = int(os.getenv("REFRESH_RATE_WINDOW", 300))

PREDICT_RATE_LIMIT = int(os.getenv("PREDICT_RATE_LIMIT", 50))
PREDICT_RATE_WINDOW = int(os.getenv("PREDICT_RATE_WINDOW", 60))


async def login_rate_limiter(request:Request , redis : Redis = Depends(get_redis_client)):
    try :
        client_ip = request.client.host

        key = f"rate:login:{client_ip}"

        current_count = await redis.get(key)

        if current_count is None:
            await redis.setex(key,LOGIN_RATE_WINDOW,1)
            auth_logger.save_logs(f"Login attempt from {client_ip}", log_level="info")
            return
    
        if int(current_count) >= LOGIN_RATE_LIMIT:
            auth_logger.save_logs(f"Rate limit exceeded for IP: {client_ip}", log_level="warning")
            raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
        await redis.incr(key)
    except RedisError:
        auth_logger.save_logs("Redis unavailable — login rate limiter bypassed", log_level="critical")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Temporarily Unavailable")

async def refresh_rate_limiter(user_id:str = Depends(get_refresh_user_id) , redis : Redis = Depends(get_redis_client)):
    try :
        
        key = f"rate:refresh:{user_id}"
        current_count = await redis.get(key)
        # redis_client returns string values

        if current_count is None:
            await redis.setex(key,REFRESH_RATE_WINDOW,1)
            auth_logger.save_logs(f"Refresh token attempt for user: {user_id}", log_level="info")
            return
    
        if int(current_count) >= REFRESH_RATE_LIMIT:
            auth_logger.save_logs(f"Rate limit exceeded for user: {user_id}", log_level="warning")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many refresh token attempts. Please try again later."
            )
        await redis.incr(key)
    except RedisError:
        auth_logger.save_logs("Redis unavailable — refresh rate limiter bypassed", log_level="critical")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Temporarily Unavailable"
        )

async def predict_rate_limiter(user_id:str = Depends(get_current_user) , redis : Redis = Depends(get_redis_client)):
    try:
        
        key = f"rate:predict:{user_id}"

        current_count = await redis.get(key)

        if current_count is None:
            await redis.setex(key,PREDICT_RATE_WINDOW,1)
            prediction_logger.save_logs(f"Prediction request from user: {user_id}", log_level="info")
            return
    
        if int(current_count) >= PREDICT_RATE_LIMIT:
            prediction_logger.save_logs(f"Rate limit exceeded for user: {user_id}", log_level="warning")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail = "Too many prediction requests. Please try again Later"
        )
    
        await redis.incr(key)
    except RedisError:
        prediction_logger.save_logs("Redis unavailable — Prediction rate limiter bypassed", log_level="critical")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Temporarily Unavailable"
        )

