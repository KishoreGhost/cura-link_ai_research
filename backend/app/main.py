from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    summary='Foundation scaffold for the Curalink medical research assistant backend.',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get('/')
async def root() -> dict[str, str]:
    return {
        'name': settings.app_name,
        'environment': settings.environment,
        'api_prefix': settings.api_v1_prefix,
        'docs_url': '/docs',
    }
