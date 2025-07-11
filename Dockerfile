# Use an official Python base
FROM python:3.11-slim

# Install OPA
RUN curl -L -o /usr/local/bin/opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64 \
  && chmod +x /usr/local/bin/opa

# Create work dir
WORKDIR /app

# Copy your code
COPY backend/ backend/
COPY scripts/ scripts/
COPY policies/ policies/
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entrypoint if you want
COPY . .

# Default command (run FastAPI for example)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
