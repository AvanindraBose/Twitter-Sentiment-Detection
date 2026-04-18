import json
from backend.core.dependencies  import get_redis_client


async def get_cached_prediction(key:str):
    try:
        redis_client = get_redis_client()
        value = await redis_client.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        print(f"Error retrieving cached prediction: {e}")
        return None

async def set_cached_prediction(key:str,value:dict , ttl:int = 300):
    try:
        redis_client = get_redis_client()
        await redis_client.setex(key,ttl,json.dumps(value))
    except Exception as e:
        print(f"Error setting cached prediction: {e}")