FROM python:3.12-slim

WORKDIR /app

COPY server.py .
COPY .env .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5555

CMD ["python", "-u", "server.py"]
