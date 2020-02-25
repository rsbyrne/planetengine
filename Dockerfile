FROM rsbyrne/base:latest

RUN git clone https://github.com/rsbyrne/everest.git
WORKDIR $WORKSPACE/everest
RUN git checkout dev
WORKDIR $WORKSPACE

RUN git clone https://github.com/rsbyrne/planetengine.git
WORKDIR $WORKSPACE/planetengine
RUN git checkout everest
WORKDIR $WORKSPACE

EXPOSE 8888
CMD ["jupyter", "notebook", "--no-browser", "--allow-root", "--ip='0.0.0.0'"]
