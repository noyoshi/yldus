FROM ubuntu:latest
MAINTAINER Noah Yoshida "nyoshida@nd.edu"
RUN apt-get update -y && apt-get install -y python3-pip python3-dev libmagick-dev

COPY . /app
ENV HOME=/app
WORKDIR /app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

RUN pip3 install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python3", "yldme.py"]
