FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY source/ ./source

EXPOSE 8000

CMD ["uvicorn", "source.app:app", "--host", "0.0.0.0", "--port", "8000"]
