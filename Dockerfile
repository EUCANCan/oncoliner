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
    liblzma-dev curl

# Install cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN . "$HOME/.cargo/env"

# Python dependencies
RUN pip install pysam pandas variant-extractor jinja2 markupsafe rjsmin rcssmin minify-html

# Copy modules and launcher script
COPY modules /oncoliner/modules
COPY shared /oncoliner/shared
COPY tools /oncoliner/tools
COPY oncoliner_launcher.py /oncoliner/oncoliner_launcher.py
