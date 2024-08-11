FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de inicio
COPY entrypoint.sh /app/entrypoint.sh

# Dar permisos de ejecución al script
RUN chmod +x /app/entrypoint.sh

# Usar el script de inicio como el comando principal
CMD ["/app/entrypoint.sh"]
