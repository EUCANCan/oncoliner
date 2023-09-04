FROM ubuntu:20.04
LABEL author="Rodrigo Martin <rodrigo.martin@bsc.es>"

ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    python3 \
    python3-pip

# Python dependencies
RUN pip install pysam pandas variant-extractor

RUN mkdir /oncoliner

# Copy modules and main script
COPY modules /oncoliner/modules
COPY main.py /oncoliner/main.py
