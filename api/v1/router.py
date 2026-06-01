"""
V1 API router — aggregates all sub-routers.
Import only this router in main.py.
"""
from fastapi import APIRouter

from api.v1 import solve, ocr, auth, health

v1_router = APIRouter()

v1_router.include_router(auth.router,   prefix="/auth",   tags=["Authentication"])
v1_router.include_router(solve.router,  prefix="/solve",  tags=["Solve"])
v1_router.include_router(ocr.router,    prefix="/ocr",    tags=["OCR"])
v1_router.include_router(health.router, prefix="/health", tags=["Health"])
