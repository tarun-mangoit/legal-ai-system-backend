# Minimal exception handlers boilerplate
from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import LegalAIException

async def custom_exception_handler(request: Request, exc: LegalAIException):
    return JSONResponse(status_code=400, content={"message": str(exc)})
