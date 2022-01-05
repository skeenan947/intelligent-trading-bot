FROM tensorflow/tensorflow:2.8.0rc0-gpu-jupyter
ADD motd /etc/motd
RUN useradd -ms /bin/bash -G sudo -u 1001 jupyter
WORKDIR /home/jupyter
ADD . app
WORKDIR /home/jupyter/app
USER root
RUN chown -R jupyter: /home/jupyter/ && pip install -r docker-requirements.txt
USER jupyter
EXPOSE 8888

CMD jupyter-lab --ip=0.0.0.0 --no-browser
