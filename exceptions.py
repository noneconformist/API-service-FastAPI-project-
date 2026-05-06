from authx.exceptions import JWTDecodeError
from fastapi.responses import JSONResponse
from jwt import ExpiredSignatureError, InvalidTokenError


def register_exception_handlers(app):
    @app.exception_handler(ExpiredSignatureError)
    async def expired_signature_handler(request, exc):
        return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request, exc):
        return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})

    @app.exception_handler(JWTDecodeError)
    async def jwt_decode_error_handler(request, exc):
        return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})
