FROM debian:sid

EXPOSE 8000

RUN apt-get update; apt-get -y install python3.12 python3-pip python3.12-venv

# Set the working directory
WORKDIR /app

# Copy application files into the container
COPY . /app

# Install Python dependencies
RUN python3.12 -m venv .venv && /app/.venv/bin/python -m pip install --no-cache-dir -r requirements.txt

# Set the MAUDE_LIB environment variable
# Adjust the paths to match where Maude and CITP are within /app
ENV MAUDE_LIB=/app/bin/Linux64:/app/bin/citp/src

# Copy the entrypoint script and set executable permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint script as the command to run
CMD ["/app/entrypoint.sh"]
