FROM ubuntu:20.04
LABEL author="Rodrigo Martin <rodrigo.martin@bsc.es>"

# Install dependencies
RUN apt-get update && apt-get upgrade -y && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    libz-dev \
    libglib2.0-dev \
    libbz2-dev \
    liblzma-dev

# Python dependencies
RUN pip install pysam pandas variant-extractor jinja2 markupsafe rjsmin rcssmin django-htmlmin

# Copy modules and launcher script
COPY modules /oncoliner/modules
COPY shared /oncoliner/shared
COPY tools /oncoliner/tools
COPY oncoliner_launcher.py /oncoliner/oncoliner_launcher.py
