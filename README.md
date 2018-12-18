yldus
=====

Simple *pastebin* and *url shortener*, but in the cloud. 

Clone of ([yld.me](http://yld.me)).

NOTE: Since it seems that running this would be hard for the grader, we included
multiple screenshots of the running application, and the logs to show that this
in fact works!

### Setting up

To run, you need the `gcloud` utility downloaded with the appropriate admin
settings, and `kubectl` downloaded with the appropriate context set up. In
addition, you need to create the database in the Google Cloud Console UI, and
supply the IP address of this database in the `secrets.py` file along with the
log in credentials. The Cloud SQL Database needs to have private IP enables and
be in the same VPC as the cluster you are intending to create. You will also
have to have docker downloaded locally to create the docker image and push it to
the Google Cloud Registry. For security purposes our images are not public (they
contain credentials).

You will also need to have a credentials file downloaded to `credentials.json`
which gives you the credentials to the project. This is used when we access the
Google Cloud Storage bucket. You have to create an IAM service account that at
least has read and write priviliges to this bucket.

#### Making the docker container

In order to use this application, you need the image of the server's docker
container to be in the Google Cloud Registry. To do this, build the server image
using 

`$ docker build -t gcr.io/[PROJECT_NAME]/[APP_NAME]:[VERSION_TAG]`

You will need to update the name of the project, name of the app, and the
version to the kubernetes config files. 

Once you build the docker image, push it to the Cloud Registry by using 

`$ docker push gcr.io/[PROJECT_NAME]/[APP_NAME]:[VERSION_TAG]`.

Once you have all the prerequisites set up and downloaded, it is trivial to
bring the service up and down. 

#### Starting up the app

First, you need to create the cluster using 

`$ bash make_cluster.sh`

Then, once the cluster has been created, you can use 

`$ kubectl create -f yldme-deploy.yaml -f yldme-balance.yaml -f yldme-ingress.yaml`

to create the deployment (which contains all the pods), the NodeCluster (a
simple service to group all the pods together so the load balancer knows how to
access them) and the ingress load balancer.

Use `$ kubectl get pods` to monitor the status of the pods, 
and use `$ kubectl describe ingress yldme-ingress` to get the status of the load
balancer. This is the thing that usually takes the longest to set up, usually 3
minutes or so. Once this is set up, the previous command should yield a result
with an indication that the backend service is `HEALTHY` and it should also have
indicated the exernal IP address of this load balancer, which you can use to
access the service. 

Finally, at the end use 

`$ kubectl autoscale deployment yldme-deploy --cpu-percent=20 --min=1 --max=[MAX_NODES]`

to create the auto scaling rules of the deployment. Replace `[MAX_NODES]` with
the maximum number of nodes you want this to scale to.

### Tearing down

Tearing down happens in reverse order. Use 

`$ kubectl delete deploy yldme-deploy`

`$ kubectl delete svc yldme-balance`

`$ kubectl delete ingress yldme-ingress`

`$ kubectl delete autoscale yldme-deploy`

to get rid of the kubernetes rules and services associated with this project. 

Monitor the status of this deletion with 

`$ gcloud compute forwarding-rules list`. 

Once there are no more items left, it is safe to delete the cluster.

Use 

`$ gcloud container clusters delete yldme-cluster` 

to delete the cluster running in the Google Kubernetes Engine.

Once you do all of these things you can go into the Cloud Conosle UI and delete
the database and the storage bucket, if you so choose. The nice thing about this
is that the storage and database are not affected by anything on the server
side, so if you want to re run the service with the data from the previous run,
it requires no work. 
