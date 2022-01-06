FROM tensorflow/tensorflow:2.8.0rc0-gpu-jupyter
RUN useradd -ms /bin/bash -G sudo -u 1001 jupyter
WORKDIR /home/jupyter
ADD . app
WORKDIR /home/jupyter/app
USER root
RUN chown -R jupyter: /home/jupyter/ && pip install -r docker-requirements.txt
USER jupyter
EXPOSE 8888
ENV SHELL=/bin/bash

CMD ./jupyter.sh
