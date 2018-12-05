#!/bin/sh


SERVICE_NAME=$1
CLUSTER_NAME=$2
# STEP 1: DEALLOCATE THE SERVICE
# Service name is the thing you called it when running kubectl run <service
# name>
kubectl delete service $SERVICE_NAME

# STEP 2: WAIT FOR LOAD BALANCER TO BE DELETED
# Watch the output from the following command:
gcloud compute forwarding-rules list

# STEP 3: DELETE THE CONTAINER CLUSTER
gcloud container clusters delete $CLUSTER_NAME 

