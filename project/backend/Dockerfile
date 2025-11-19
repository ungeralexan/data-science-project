ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Start FastAPI via uvicorn
# We have app.py with "app = FastAPI()", so the target is "app:app"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
