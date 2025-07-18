FROM python:3.11-slim

WORKDIR /data/rrweb

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r /tmp/requirements.txt

# COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
