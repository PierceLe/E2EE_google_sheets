from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from exception.error_code import ErrorCode
from exception.app_exception import AppException
from dto.response.error_response import ErrorResponse

# Handling AppException
async def app_exception_handler(request: Request, exc: AppException):
    error_response = ErrorResponse(code=exc.error_code.code, error_message=exc.error_code.error_message)
    return JSONResponse(
        status_code=200,
        content=error_response.dict()
    )

# Handling HTTPException
async def http_exception_handler(request: Request, exc: HTTPException):
    error_response = ErrorResponse(code=exc.status_code, error_message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

def get_http_exception_response(exc: HTTPException) -> JSONResponse:
    error_response = ErrorResponse(code=exc.status_code, error_message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    ) 