FROM gcr.io/kaggle-gpu-images/python

EXPOSE 8888
ENV SHELL=/bin/bash

RUN useradd -ms /bin/bash -G sudo -u 1001 jupyter
ADD docker-requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt
