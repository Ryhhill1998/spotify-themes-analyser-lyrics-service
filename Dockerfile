FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

EXPOSE 8080
CMD ["fastapi", "run", "lyrics_api/main.py", "--port", "8080"]
