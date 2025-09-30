import os
import uvicorn
from dotenv import load_dotenv

# note: VS Code's Python extension might falsely report an unresolved import
from app import create_app
from app.config import settings

if __name__ == "__main__":
    load_dotenv()

    if settings.is_development:
        # Use import string for reload mode
        uvicorn.run(
            "app:create_app",
            host=settings.host,
            port=settings.port,
            log_level="info",
            reload=True,
            factory=True,
        )
    else:
        # Use app object for production
        app = create_app()
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level="warning",
            reload=False,
        )
