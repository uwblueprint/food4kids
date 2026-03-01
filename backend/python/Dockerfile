FROM python:3.11

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "cd /app && alembic upgrade head && python server.py"]
