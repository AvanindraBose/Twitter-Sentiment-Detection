import json
from backend.core.dependencies  import get_redis_client
from backend.logging_fastapi.logger_api import prediction_logger
from backend.custom_metrics import CACHE_HIT, CACHE_MISS, CACHE_WRITES

async def get_cached_prediction(key:str):
    try:
        redis_client = await get_redis_client()
        value = await redis_client.get(key)
        if value:
            # record cache hit
            try:
                CACHE_HIT.labels(endpoint="/predict").inc()
            except Exception:
                pass
            return json.loads(value)
        else:
            # record cache miss
            try:
                CACHE_MISS.labels(endpoint="/predict").inc()
            except Exception:
                pass
            return None
    except Exception as e:
        prediction_logger.save_logs(f"Error retrieving cached prediction: {e}", log_level="error")
        return None

async def set_cached_prediction(key:str,value:dict , ttl:int = 300):
    try:
        redis_client = await get_redis_client()
        await redis_client.setex(key,ttl,json.dumps(value))
        # record cache write
        try:
            CACHE_WRITES.labels(endpoint="/predict").inc()
        except Exception:
            pass
        prediction_logger.save_logs(f"Cached prediction set with key", log_level="info")
    except Exception as e:
        prediction_logger.save_logs(f"Error setting cached prediction: {e}", log_level="error")