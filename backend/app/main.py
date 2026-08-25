from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router
from app.routers.kpis import router as kpis_router
from app.routers.sites import router as sites_router
from app.routers.parts import router as parts_router
from app.routers.suppliers import router as suppliers_router
from app.routers.root_cause import router as root_cause_router
from app.routers.register_user import router as register_user_router
from app.routers.login import router as login_router
from app.routers.logout import router as logout_router
from app.routers.api_me import router as api_me_router

app = FastAPI(
    title='ReadinessIQ API',
    description='Logistics readiness and supply visibility backend API',
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

_default_cors = 'http://localhost:5173,http://127.0.0.1:5173'
_cors_origins = os.environ.get('CORS_ORIGINS', _default_cors)
_allow_origins = [o.strip() for o in _cors_origins.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(kpis_router)
app.include_router(sites_router)
app.include_router(parts_router)
app.include_router(suppliers_router)
app.include_router(root_cause_router)
app.include_router(register_user_router)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(api_me_router)

@app.get('/')
async def root():
    return {'message': 'Hello ReadinessIQ'}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)