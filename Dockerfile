FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "3", "WebMaude.wsgi:application", "-b", "0.0.0.0:8000"]

