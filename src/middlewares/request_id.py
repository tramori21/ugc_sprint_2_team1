from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-Id"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name)

        if not request_id:
            return JSONResponse(status_code=400, content={"detail": "X-Request-Id is required"})

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers[self.header_name] = request_id

        try:
            span = trace.get_current_span()
            if span and span.is_recording():
                span.set_attribute("http.request_id", request_id)
        except Exception:
            pass

        return response
