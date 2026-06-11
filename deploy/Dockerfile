FROM python:3.12-slim

# System deps for cartopy / GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev libproj-dev proj-data proj-bin \
    libeccodes-dev \
    supercronic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run pipeline every 6 hours (matches AROME run cadence)
RUN echo "0 */6 * * * /app/run_all.sh >> /var/log/meteo.log 2>&1" > /etc/crontab.txt

CMD ["supercronic", "/etc/crontab.txt"]
