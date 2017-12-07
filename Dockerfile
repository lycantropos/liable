ARG PYTHON3_VERSION

FROM python:${PYTHON3_VERSION}

WORKDIR /opt/liable

COPY liable.py liable.py
COPY tests/ tests/
COPY README.rst .
COPY setup.py .
COPY setup.cfg .

RUN python3 -m pip install -e .
