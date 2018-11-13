#!/bin/sh

# STEP 1: CONFIGS
# First, do this to get the project id
export PROJECT_ID="$(gcloud config get-value project -q)"
export APP_NAME=$1
export CLUSTER_NAME=$2
export SERVICE_NAME=$3

# STEP 2: BUILD IMAGE
# Builds the image for this container... change hello-app to change the name or
# v1 to change the tag
docker build -t gcr.io/${PROJECT_ID}/$APP_NAME:v1 .

# check to see if it build correctly
# $ docker images

# STEP 3: PUSH IMAGE TO GKE
# if you have not configured gcloud and docker to communicate
# gcloud auth configure-docker

# push our image to the gke container registry
docker push gcr.io/${PROJECT_ID}/$APP_NAME:v1

# STEP 4: CREATE WORKERS (the vms running the actual containers)
# create a cluster of nodes (vms?)
gcloud container clusters create $CLUSTER_NAME --num-nodes=3

# see the worker VM instances we created
# gcloud compute instances list

# STEP 5: DEPLOY APPLICATION
# deploy the application, using port 8080
kubectl run hello-web --image=gcr.io/${PROJECT_ID}/$APP_NAME:v1 --port 8080

# see if pods were created
# kubectl get pods

# STEP 6: EXPOSE APPLICATION (and use load balancer)
# Make sure target-port matches the port used in part 5
# --port specifies the port the load balancer should listen on
kubectl expose deployment $SERVICE_NAME --type=LoadBalancer --port 80 --target-port 8080

# Get the IP address of our load balancer
kubectl get service

# TODO STEP 7: SCALE UP 

# TODO STEP 8: UPDATE APPS WITH NEW CODE (CI/CD)

echo "using app named: $APP_NAME"
echo "using cluster named $CLUSTER_NAME"
echo "using service named: $SERVICE_NAME"



