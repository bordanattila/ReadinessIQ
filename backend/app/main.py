from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.kpis import router as kpis_router
from app.routers.sites import router as sites_router
from app.routers.parts import router as parts_router

app = FastAPI(
    title='ReadinessIQ API',
    description='Logistics readiness and supply visibility backend API',
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.include_router(health_router)
app.include_router(kpis_router)
app.include_router(sites_router)
app.include_router(parts_router)

@app.get('/')
async def root():
    return {'message': 'Hello World'}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)