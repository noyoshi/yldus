FROM ubuntu:latest
MAINTAINER Noah Yoshida "nyoshida@nd.edu"
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev

COPY . /app
ENV HOME=/app
WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python3", "yldme.py"]
