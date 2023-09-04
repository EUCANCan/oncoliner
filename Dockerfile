FROM ubuntu:20.04
LABEL author="Rodrigo Martin <rodrigo.martin@bsc.es>"

RUN export DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    python3 \
    python3-pip \
    libz-dev \
    libglib2.0-dev \
    libbz2-dev \
    liblzma-dev

# Python dependencies
RUN pip install pysam pandas variant-extractor

# Copy modules and main script
COPY modules /oncoliner/modules
COPY main.py /oncoliner/main.py
