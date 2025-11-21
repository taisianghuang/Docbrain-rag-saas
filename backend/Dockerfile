FROM python:3.11-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir fastapi uvicorn[standard] langchain openai chromadb python-multipart aiofiles pypdf python-dotenv requests

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
