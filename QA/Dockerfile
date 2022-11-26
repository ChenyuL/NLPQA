# Ubuntu Linux as the base image
FROM ubuntu:22.04

# Set UTF-8 encoding
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install Python
RUN apt-get -y update && \
    apt-get -y upgrade

# The following line ensures that subsequent install doesn't expect user input
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install python3-pip python3-dev

# Install spaCy
RUN pip3 install --upgrade pip
RUN pip3 install spacy
RUN python3 -m spacy download en_core_web_sm
RUN pip3 install protobuf==3.20.1

# Haystack for QA
RUN pip3 install farm-haystack

# Add the files into container, under QA folder, modify this based on your need
RUN mkdir /QA
ADD answer /QA

RUN mkdir /QA/saveDocs

CMD ["chmod 777 /QA/*"]

# Set working dir as /QA
WORKDIR /QA

ENTRYPOINT ["/bin/bash", "-c"]