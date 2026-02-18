FROM python:3.12-slim AS builder 
WORKDIR /app 

ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONBUFFERED=1

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim 
WORKDIR /app 

COPY --from=builder /opt/venv /opt/venv 

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY app/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
