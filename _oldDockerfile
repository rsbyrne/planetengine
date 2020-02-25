FROM rsbyrne/base:latest

RUN apt-get -y install sudo
RUN useradd -m jovyan && echo "jovyan:jovyan" | chpasswd && adduser jovyan sudo
RUN chown jovyan $WORKSPACE
USER jovyan

EXPOSE 8888
CMD ["jupyter", "notebook", "--no-browser", "--allow-root", "--ip='0.0.0.0'"]
