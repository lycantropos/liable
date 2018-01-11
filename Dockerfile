ARG PYTHON3_VERSION

FROM python:${PYTHON3_VERSION}

WORKDIR /opt/liable

ENV LANG=en_US.UTF-8

COPY scripts/ scripts/
COPY tests/ tests/
COPY README.rst .
COPY setup.py .
COPY setup.cfg .

RUN python3 -m pip install -e .
RUN python3 -m nltk.downloader wordnet
