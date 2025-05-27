FROM python:3.12.9

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY API.py /app
COPY logs/ /app/logs/

EXPOSE 8888

CMD ["uvicorn", "API:app", "--host", "0.0.0.0", "--port", "8888"]
