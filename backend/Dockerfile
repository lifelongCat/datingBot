FROM python:3.11

WORKDIR /backend

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

CMD alembic upgrade head \
    && mkdir -p prometheus-multiprocess \
    && export PROMETHEUS_MULTIPROC_DIR=$(pwd)/prometheus-multiprocess \
    && uvicorn app.main:app --host "0.0.0.0" --port 8080 --reload
