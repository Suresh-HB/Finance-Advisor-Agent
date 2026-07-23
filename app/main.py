from fastapi import FastAPI

from app.api.routes import router
from app.config import config
from app.middleware.error_handler import add_exception_handlers
from app.utils.data_generator import generate_synthetic_data_if_missing
from app.utils.logger import logger


def create_app() -> FastAPI:
    app = FastAPI(title=config.app_name, version=config.app_version)
    add_exception_handlers(app)
    app.include_router(router)

    @app.on_event("startup")
    def startup_event() -> None:
        generate_synthetic_data_if_missing()
        logger.info("Application startup complete")

    return app


app = create_app()
