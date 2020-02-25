FROM rsbyrne/base:latest

EXPOSE 8888
CMD ["jupyter", "notebook", "--no-browser", "--allow-root", "--ip='0.0.0.0'"]
