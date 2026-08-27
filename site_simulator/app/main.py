from fastapi import FastAPI

from app.routes.shipments import router as shipments_router

app = FastAPI(
    title='Site Simulator API',
    description='Site simulator backend API',
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.include_router(shipments_router)

@app.get('/')
async def root():
    return {'message': 'Hello Site Simulator'}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=9000)