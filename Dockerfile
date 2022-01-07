# syntax=docker/dockerfile:1
FROM tensorflow/tensorflow:2.8.0rc0-gpu-jupyter AS builder
USER root
RUN mkdir /build
WORKDIR /build
RUN apt -q update && apt -qy install cmake && \
    git clone --recursive https://github.com/microsoft/LightGBM && \
    cd LightGBM && \
    mkdir build && \
    cd build && \
    cmake -DUSE_CUDA=1 .. && \
    make -j4


FROM tensorflow/tensorflow:2.8.0rc0-gpu-jupyter
WORKDIR /app
ADD docker-requirements.txt .
COPY  --from=builder /build/LightGBM/lib_lightgbm.so /usr/local/lib/python3.8/dist-packages/lightgbm/lib_lightgbm.so
RUN apt -q update && apt -qy install nodejs && \
    pip install -r docker-requirements.txt && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* ~/* && \
    jupyter labextension install jupyterlab-nvdashboard && \
    curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz && \
    mkdir -p /opt/gcloud && \
    tar -C /opt/gcloud -xvf /tmp/google-cloud-sdk.tar.gz && \
    /opt/gcloud/google-cloud-sdk/install.sh && \
    rm /tmp/google-cloud-sdk.tar.gz

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

EXPOSE 8888

CMD jupyter-lab --allow-root --ip=0.0.0.0 --no-browser
