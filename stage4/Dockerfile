# One image for the gateway and the device emulators (E10 testbed).
# The gateway needs torch (detector) + web3 (optional EVM ledger); devices need only numpy + paho,
# but share the image so the laptop builds once. ztfl/src is bind-mounted at /src for models.py and
# ledger.py; the stage-4 app code is baked in.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONPATH=/app:/src

# Trust the laptop's HTTPS-inspection root if present (Avast / corporate proxy); empty is fine.
COPY certs/ /usr/local/share/ca-certificates/
RUN update-ca-certificates && echo "PIP_CERT=/etc/ssl/certs/ca-certificates.crt" >> /etc/environment
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0 \
 && pip install numpy "paho-mqtt<2" web3==7.16.0

WORKDIR /app
COPY common.py /app/common.py
COPY gateway/app.py /app/gateway_app.py
COPY device/app.py /app/device_app.py
