#!/bin/bash
gcloud container clusters create yldme-cluster \
 --enable-ip-alias \
 --zone us-central1-b \
 --create-subnetwork="" \
 --network=default \
 --node-locations us-central1-b \
 --num-nodes 2 --enable-autoscaling --min-nodes 1 --max-nodes 10 \
 --addons HorizontalPodAutoscaling,HttpLoadBalancing
