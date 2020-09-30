FROM underworldcode/uw2cylindrical:cylindrical

USER root

RUN easy_install pip
RUN pip install --no-cache-dir -U h5py

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y nano
RUN apt-get install -y ffmpeg

RUN pip install --no-cache-dir pandas
RUN pip install --no-cache-dir dask[complete]
RUN pip install --no-cache-dir scikit-learn

# Productivity
RUN pip install --no-cache-dir jupyterlab

# Programming
RUN apt-get install -y graphviz
RUN pip install --no-cache-dir objgraph
RUN pip install --no-cache-dir xdot

ENV PYTHONPATH "${PYTHONPATH}:/home/jovyan/workspace"

USER $NB_USER

RUN umask 0000
