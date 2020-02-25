FROM underworldcode/uw2cylindrical:cylindrical

USER root

RUN easy_install pip
RUN pip install -U h5py

USER $NB_USER

RUN umask 0000

CMD ["jupyter", "notebook", "--ip='0.0.0.0'", "--no-browser", '--allow-root']
