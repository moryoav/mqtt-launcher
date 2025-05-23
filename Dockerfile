FROM python:3.13-slim

LABEL maintainer="moryoav"
LABEL description="MQTT Launcher - Execute shell commands triggered by MQTT messages"

ARG APT_INSTALL
ARG PIP_INSTALL
ARG PIP_UPDATE=false
ARG APT_UPDATE=false

# Update system and install dependencies
RUN if [ "$APT_UPDATE" = "true" ] ; then \
        apt-get update && \
        apt-get upgrade -y ; \
    else \
        apt-get update ; \
    fi && \
    apt-get install -y git $APT_INSTALL && \
    rm -rf /var/lib/apt/lists/*

# Update pip and install Python packages
RUN if [ "$PIP_UPDATE" = "true" ] ; then \
        python -m pip install --upgrade pip ; \
    fi && \
    if [ "$PIP_INSTALL" != "" ] ; then \
        pip install $PIP_INSTALL ; \
    fi

# Install mqtt-launcher
WORKDIR /mqtt-launcher
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /mqtt-launcher/entrypoint.sh
RUN chmod +x /mqtt-launcher/entrypoint.sh

ENTRYPOINT ["/mqtt-launcher/entrypoint.sh"]
#ENTRYPOINT ["python","mqtt-launcher.py"]
