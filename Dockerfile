FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
VOLUME /app/data
ENTRYPOINT python3 main.py