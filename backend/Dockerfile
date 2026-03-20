FROM python:3.11-slim

WORKDIR /app

COPY ./app ./app
COPY ./requirements.txt ./requirements.txt
COPY ./data ./data

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]