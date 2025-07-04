# Use the official Ubuntu base image
FROM ubuntu:22.04

# Set environment variables to non-interactive to avoid prompts during installation
# 环境变量设置
ARG http_proxy
ARG https_proxy
ENV http_proxy=$http_proxy \
    https_proxy=$https_proxy \
    DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages
RUN apt-get update && \
    apt-get install -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.10 \
        python3.10-venv \
        python3.10-distutils \
        python3-pip \
        wget \
        git \
        libgl1 \
        libreoffice \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        ttf-mscorefonts-installer \
        fontconfig \
        libglib2.0-0 \
        libxrender1 \
        libsm6 \
        libxext6 \
        poppler-utils \
        && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Create a virtual environment for MinerU
RUN python3 -m venv /opt/mineru_venv

# Copy the configuration file template and install magic-pdf latest
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install --upgrade pip && \
    pip3 install -U magic-pdf[full]"

# Download models and update the configuration file
COPY magic-pdf.json /root/magic-pdf.json
RUN /bin/bash -c "pip3 install modelscope && \
    wget https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/scripts/download_models.py -O download_models.py && \
    python3 download_models.py && \
    sed -i 's|cpu|cuda|g' /root/magic-pdf.json"

COPY app.py /app/app.py
RUN /bin/bash -c "source /opt/mineru_venv/bin/activate && \
    pip3 install fastapi uvicorn python-multipart loguru"


# Set the entry point to activate the virtual environment and run the command line tool
ENTRYPOINT ["/bin/bash", "-c", "source /opt/mineru_venv/bin/activate && exec \"$@\"", "--"]
