import json
from backend.core.dependencies  import get_redis_client
from src.logger_class import CustomLogger,create_log_path

prediction_logger = CustomLogger(
    logger_name="prediction",
    log_filename=create_log_path("prediction")
)

async def get_cached_prediction(key:str):
    try:
        redis_client = get_redis_client()
        value = await redis_client.get(key)
        prediction_logger.save_logs(f"Retrieved cached prediction.", log_level="info")
        return json.loads(value) if value else None
    except Exception as e:
        prediction_logger.save_logs(f"Error retrieving cached prediction: {e}", log_level="error")
        return None

async def set_cached_prediction(key:str,value:dict , ttl:int = 300):
    try:
        redis_client = get_redis_client()
        await redis_client.setex(key,ttl,json.dumps(value))
        prediction_logger.save_logs(f"Cached prediction set with key", log_level="info")
    except Exception as e:
        prediction_logger.save_logs(f"Error setting cached prediction: {e}", log_level="error")