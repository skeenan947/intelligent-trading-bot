FROM tensorflow/tensorflow:2.8.0rc0-gpu-jupyter
RUN useradd -ms /bin/bash -G sudo -u 1001 jupyter
ADD . /app
WORKDIR /app
USER root
RUN chown -R jupyter: /app && \
    apt -q update && apt -qy install nodejs && \
    pip install -r docker-requirements.txt && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* ~/*
USER jupyter
RUN jupyter labextension install jupyterlab-nvdashboard
EXPOSE 8888
ENV SHELL=/bin/bash

CMD ./jupyter.sh
