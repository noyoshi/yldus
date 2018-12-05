yldme
=====

Simple *pastebin* and *url shortener* ([yld.me](http://yld.me)).

NOTE: You have to use `gcloud create cluster...` before using
`kubectl create -f ...`, and in the `yaml` files you need to 
set the appropriate IP address for the NFS file server - else 
the initialization will fail. You also need to make sure that you 
have the NFS single node file server up and running beforehand.
I think that the internal IP for this NFS server will be the same
every time - but check to make sure.
