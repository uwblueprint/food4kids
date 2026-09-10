FROM python:3.11

WORKDIR /app

# Production by default: only requirements.txt is installed, so the deployed
# image carries no linters, test runners, type stubs or plotting libraries.
# Local development and CI pass INSTALL_DEV=true to add requirements-dev.txt
# (docker-compose.yml sets it). Keep the default false -- the CI boot smoke
# builds without it precisely so a runtime dependency misfiled as a dev
# dependency fails there rather than in production.
ARG INSTALL_DEV=false

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         pip install --no-cache-dir -r requirements-dev.txt; \
       fi

COPY . ./

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "cd /app && alembic upgrade head && python server.py"]
