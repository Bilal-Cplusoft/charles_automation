FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=9000", "--server.address=0.0.0.0"]
