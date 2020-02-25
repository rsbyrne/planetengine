FROM underworldcode/uw2cylindrical:cylindrical

RUN easy_install pip
RUN pip install -U h5py
