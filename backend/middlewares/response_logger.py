import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger("response_logger")

class ResponseLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request : Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = round((time.time() - start_time)*1000 , 2)
        logger.info(
            "method=%s path=%s status_code=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            process_time
        )

        return response