from fastapi import FastAPI
from app.config import load_configurations, configure_logging

def create_app():
    app = FastAPI()

    configure_logging()  # Initialize logging
    load_configurations(app)  # Load configurations into app state

    return app

app = create_app()
