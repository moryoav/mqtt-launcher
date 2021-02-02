FROM python:3.9.1-slim

MAINTAINER IlmLV

ARG APT_INSTALL
ARG PIP_INSTALL

RUN apt-get update && \
  apt-get install -y git $APT_INSTALL && \
  rm -rf /var/lib/apt/lists/*

RUN if [ "$PIP_INSTALL" != "" ] ; then \
        pip install $PIP_INSTALL ; \
    fi
    
RUN git clone https://github.com/IlmLV/mqtt-launcher && \
  cd mqtt-launcher && \
  pip install -r requirements.txt

WORKDIR mqtt-launcher

COPY entrypoint.sh /mqtt-launcher/entrypoint.sh

ENTRYPOINT ["/mqtt-launcher/entrypoint.sh"]
#ENTRYPOINT ["python","mqtt-launcher.py"]
