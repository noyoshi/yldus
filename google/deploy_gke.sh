#!/bin/sh
# TODO NOTES:
# kubectl create -f <filename> can replace any kubectl command, when you give
# it the correct yaml file with the specs of the thing you want to create..
# This DOES NOT replace any `gcloud` commands you would run...

# STEP 1: CONFIGS
# First, do this to get the project id
export PROJECT_ID="$(gcloud config get-value project -q)"
export APP_NAME=$1
export CLUSTER_NAME=$2

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

# TODO Autoscaling:
# gcloud container clusters create example-cluster \
# --zone us-central1-a \
# --node-locations us-central1-a,us-central1-b,us-central1-f \
# --num-nodes 2 --enable-autoscaling --min-nodes 1 --max-nodes 4
# Above would create nodes in all of those locations, with each location
# starting with 2 nodes, and scaling between 1 and 4 nodes each (total 3 - 12
# nodes)

# TODO NOTE:
# When scaling down, cluster autoscaler respects scheduling and eviction rules set on Pods. These restrictions can prevent a node from being deleted by the autoscaler. A node's deletion could be prevented if it contains a Pod with any of these conditions:

# The Pod's affinity or anti-affinity rules prevent rescheduling.
# The Pod has local storage.
# The Pod is not managed by a Controller such as a Deployment, StatefulSet, Job or ReplicaSet.
# An application's PodDisruptionBudget can also prevent autoscaling; if deleting nodes would cause the budget to be exceeded, the cluster does not scale down.

# see the worker VM instances we created
# gcloud compute instances list

# STEP 5: DEPLOY APPLICATION
# deploy the application, using port 8080
kubectl run hello-web --image=gcr.io/${PROJECT_ID}/$APP_NAME:v1 --port 8080
# TODO change this to use a yaml instead, and be invoked using kubectl
# create -f

# see if pods were created
# kubectl get pods

# STEP 6: EXPOSE APPLICATION (and use load balancer)
# Make sure target-port matches the port used in part 5
# --port specifies the port the load balancer should listen on
kubectl expose deployment $APP_NAME --type=LoadBalancer --port 80 --target-port 8080
# TODO I think this can be replaced by using kubectl and a custom yaml file
# that will 1. create a replication controller (what this is already doing i
# think?) and 2. mount the file system on this? The example yaml does not seem
# to contain anything about the file system in the yaml that would replace
# step 5...

# Get the IP address of our load balancer
kubectl get service

# TODO STEP 7: SCALE UP 

# TODO STEP 8: UPDATE APPS WITH NEW CODE (CI/CD)

echo "using app named: $APP_NAME"
echo "using cluster named $CLUSTER_NAME"



