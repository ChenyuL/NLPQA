# Ubuntu Linux as the base image. You can use any version of Ubuntu here
FROM ubuntu:18.04

EXPOSE 8000
# Set UTF-8 encoding
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

WORKDIR /home/user/
# Install Python
RUN apt-get -y update && \
apt-get -y upgrade
# The following line ensures that the subsequent install doesn't expect user input
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install python3-pip python3-dev
RUN apt-get -y install git
COPY requirements.txt /home/user/
# Install dependencies
RUN pip3 install --upgrade pip

RUN pip3 install spacy
RUN python3 -m spacy download en_core_web_sm

RUN pip3 install --user -U nltk
RUN pip3 install --upgrade pip
#RUN pip3 install git+https://github.com/deepset-ai/haystack.git#egg=farm-haystack
RUN pip install -r requirements.txt
# Add the files into container, under QA folder, modify this based on your need
RUN mkdir /QA
ADD answer /QA

RUN mkdir /QA/saveDocs


# Change the permissions of programs
CMD ["chmod 777 /QA/*"]
# Set working dir as /QA
WORKDIR /QA

ENTRYPOINT ["/bin/bash", "-c"]