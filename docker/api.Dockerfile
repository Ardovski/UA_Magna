# syntax=docker/dockerfile:1.7
FROM python:3.12-alpine AS deps
WORKDIR /app
COPY apps/api/requirements.txt apps/api/requirements-dev.txt ./
RUN apk add --no-cache --virtual .build-deps gcc musl-dev g++ && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local/lib/python3.12/site-packages -type d \( \
        -name "tests" -o -name "test" -o -name "__pycache__" -o -name "*-info" -o -name "_pyinstaller" \
    \) -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.12/site-packages/pip /usr/local/lib/python3.12/site-packages/setuptools 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.12/site-packages/numpy/f2py /usr/local/lib/python3.12/site-packages/numpy/testing /usr/local/lib/python3.12/site-packages/pandas/conftest.py /usr/local/lib/python3.12/site-packages/pandas/_version_meson.py 2>/dev/null || true

FROM python:3.12-alpine AS runner
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apk add --no-cache curl
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY apps/api/app ./app
COPY docker/entrypoint-api.sh /usr/local/bin/entrypoint-api.sh
RUN chmod +x /usr/local/bin/entrypoint-api.sh
RUN mkdir -p /app/var
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint-api.sh"]
