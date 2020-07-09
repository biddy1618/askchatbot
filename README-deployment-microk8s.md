# Deploy the chatbot w MicroK8s

- This method is used to deploy the QA chatbot at http://35.166.13.105:8001/

### Install microk8s with required addons ([docs](https://microk8s.io/docs)) 

```bash
# check for the version
snap info microk8s 

# install latest/stable version
sudo snap install microk8s --classic

# join the microk8s group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube
su - $USER # or relogin

# use add-ons 
microk8s status
microk8s enable dns storage helm3 registry 
```

To start & stop  (Or do anything else see the [microk8s command reference](https://microk8s.io/docs/commands))

```bash
# stop/start with
microk8s stop
microk8s start

# To get the details of the nodes 
microk8s kubectl get nodes -o wide

# To uninstall & remove microk8s
sudo snap remove microk8s
```



### Install Rasa X with AskChatbot

[Rasa X docs on using helm](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/) & [Rasa X Helm Chart repository](https://github.com/rasahq/rasa-x-helm)

#### Build docker image for action server

Docs for [Using the build-in registry](https://microk8s.io/docs/registry-built-in)

- Make sure that the build-in registry is enabled:

  ```bash
  microk8s enable registry
  ```

- Build docker image with correct tag 

  ```bash
  # get latest version of the github repo
  git status
  git stash push
  git pull
  git stash pop
  
  # build docker image
  sudo docker-compose build
  
  # then tag it for use in the microk8s built-in registry
  sudo docker images
  sudo docker tag 1fe3d8f47868 localhost:32000/askchatbot-action-server:0.0.2
  
  # To quickly test that the container starts up
  sudo docker run -p 5055:5055 --add-host ask-chat-db-dev.i.eduworks.com:34.211.141.190 localhost:32000/askchatbot-action-server:0.0.2
  
  curl http://<hostname>:5055/actions
  ```

- Push the docker image into the built-in registry of the microk8s cluster

  ```bash
  sudo docker push localhost:32000/askchatbot-action-server
  ```


#### Make kubernetes cluster accessible & set some aliases

```bash
#####################################################
# It is recommended to add these to your ~/.bashrc  #
#####################################################

alias kubectl='microk8s.kubectl'
alias helm='microk8s.helm3'

# set aliases for using kubectl in a namespace
alias k="kubectl --namespace my-namespace"

# set aliases for using helm  in a namespace
alias h="helm --namespace my-namespace"
```

After you added these to your ~/.bashrc, don't forget to run:

```bash
source ~/.bashrc
```



#### Create the Kubernetes name-space

```bash
# Verify all is in place
kubectl version --short --client
kubectl version --short
helm version

# Create the namespaces
kubectl create namespace my-namespace
```



#### Define `values.yml` ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#quick-install))

On the ec2 instance, you can find the file at:

```bash
/home/abuijk/repos/askchatbot/deploy/kubernetes/secret/values.yml
```

The file was created using these [instructions](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#deploy-to-a-cluster-rasa-enterprise), with a few additional comments & tips are given below:

###### Debug mode

Edit `values.yml` to contain the contents below

```bash
# use Debug or not
debugMode: "false"
```

###### nginx service: `port`, `externalIPs`

Edit `values.yml` to contain the contents below. This will create the default `rasa/nginx` service of type `LoadBalancer `, and expose it to the `externalIPs`, which is in this case is the IP of the EC2 instance.

```bash
# nginx specific settings
nginx:
  service:
    type: LoadBalancer
    port: 8001
    # hostname -I
    externalIPs: [10.1.100.167]
```

###### (Step 7) Configure the custom action server

Add this to your `values.yml` 

```bash
app:
    # microk8s build-in registry
    name: "localhost:32000/askchatbot-action-server"
    tag: "0.0.2"
```

#### Deploy  ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#quick-install))

##### Initial deployment with helm

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Deploy
h install my-release --values values.yml rasa-x/rasa-x
=> do not forget to upload the model
```

###### Add `hostAliases` to `my-release-app` deployment

In order for the action server to know the IP address of the elastic-search instance, an entry must be added to the `hosts` file of the container. In Kubernetes, this is accomplished with `hostAliases`, which is identical to `extra_hosts` of docker-compose:

- [Adding host aliases to deployments](https://serverfault.com/a/895213/562905)
- [Adding entries to Pod /etc/hosts with HostAliases](https://kubernetes.io/docs/concepts/services-networking/add-entries-to-pod-etc-hosts-with-host-aliases/)

After all the pods are running, edit the `my-release-app` deployment with:

```bash
######################################################################
# before: check content of /etc/hosts in the action server container #
######################################################################
k exec my-release-app-778464c7bc-mcxq2 -- cat /etc/hosts
>
# Kubernetes-managed hosts file.
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
fe00::0	ip6-mcastprefix
fe00::1	ip6-allnodes
fe00::2	ip6-allrouters
10.1.67.35	my-release-app-778464c7bc-mcxq2

###################
# Add hostAliases #
###################
k get deployments

k edit deployment my-release-app
> Add this to the pod template spec section:
spec:
.
  template:
  .
    spec:
      hostAliases:
       - ip: 34.211.141.190
         hostnames:
         - ask-chat-db-dev.i.eduworks.com
      containers:
      - image: localhost:32000/askchatbot-action-server:0.0.2
        .

#####################################################################
# after: check content of /etc/hosts in the action server container #
#####################################################################
k exec my-release-app-778464c7bc-mcxq2 -- cat /etc/hosts
>
# Kubernetes-managed hosts file.
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
fe00::0	ip6-mcastprefix
fe00::1	ip6-allnodes
fe00::2	ip6-allrouters
10.1.67.35	my-release-app-778464c7bc-mcxq2

# Entries added by HostAliases.
34.211.141.190	ask-chat-db-dev.i.eduworks.com
```

##### Initial deployment with kubectl

Due to long start-up time of the action server, it might be needed to use this approach, so you can patch up the kubernetes objects prior to deployment

```bash
# Create deployment yaml
h template --values values.yml my-release rasa-x/rasa-x > rasa-x-deployment.yml

# Add a Startup Probe for the action server
# https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-startup-probes
# Allow 5 minutes for startup
        startupProbe:
          httpGet:
            path: /health
            port: "http"
          failureThreshold: 30
          periodSeconds: 10

# Add hostAliases to the pod template spec section:
spec:
.
  template:
  .
    spec:
      hostAliases:
       - ip: 34.211.141.190
         hostnames:
         - ask-chat-db-dev.i.eduworks.com
      containers:
      - image: localhost:32000/askchatbot-action-server:0.0.2
        .

# check correctness of yaml
k create --dry-run=client -f rasa-x-deployment.yml

# deploy from the yaml
k create -f rasa-x-deployment.yml
=> do not forget to upload the model

# to update after modifying a resource
k apply -f rasa-x-deployment.yml

# to delete all the resources
k delete -f rasa-x-deployment.yml

# sometimes, to fully clean things up, you have to delete & recreate the namespace
kubectl delete namespaces my-namespace
kubectl get namespaces # wait till it is gone
kubectl create namespace my-namespace
```



##### Upgrade deployment with helm

When `values.yml` was changed, just issue these commands:

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Upgrade
h upgrade my-release --values values.yml --reuse-values rasa-x/rasa-x
```

##### Apply deployment changes with kubectl

When you have a modification to `rasa-x-deployment.yml` , issue this command to apply the changes:

```bash
# to update after modifying a resource
k apply -f rasa-x-deployment.yml
=> do not forget to upload the model
```

##### Redeploy a new action server

When the tag changed, just update `values.yml` and redeploy as described above.

If the tag has not changed, then you must restart the app's deployment, by scaling it down and back up

```bash
# k get deployments
k scale deployment my-release-app --replicas=0  # wait until it is gone
k scale deployment my-release-app --replicas=1
=> do not forget to upload the model
```



#### Check deployment progress

Note that it takes a while before all the pods are running. Especially the r`asa-production` pod takes awhile to start up due to the large image file to be download. 

The following commands are very useful to monitor the deployment progress.

```bash
k get pods
k describe pods my-release-rasa-production-6b9c5d5f75-7j87s

# The nginx loadbalancer service:
# -> EXTERNAL-IP is the value of externalIPs, which we set to the host's IPv4-Internal, from `hostname -I`
# -> PORT = 8001:<-->/TCP, which indicates that the host's port 8001 is forwarded to the cluster's port <-->
# -> If you open up port 8001 for external TCP traffic, you will be able to reach Rasa X from the outside
k get services
>
NAME                              TYPE         CLUSTER-IP      EXTERNAL-IP     PORT(S)
my-release-postgresql             ClusterIP    10.152.183.39   <none> 5432/TCP
my-release-postgresql-headless    ClusterIP    None            <none>          5432/TCP                             
my-release-rabbit                 ClusterIP    10.152.183.14   <none>          4369/TCP,5672/TCP,25672/TCP,15672/TCP
my-release-rabbit-headless        ClusterIP    None            <none>          4369/TCP,5672/TCP,25672/TCP,15672/TCP
my-release-rasa-x-app             ClusterIP    10.152.183.22   <none>          5055/TCP,80/TCP                      
my-release-rasa-x-duckling        ClusterIP    10.152.183.115  <none>          8000/TCP                            
my-release-rasa-x-nginx           LoadBalancer 10.152.183.15   10.1.100.167    8001:32152/TCP                      
my-release-rasa-x-rasa-production ClusterIP    10.152.183.21   <none>          5005/TCP                           
my-release-rasa-x-rasa-worker     ClusterIP    10.152.183.163  <none>          5005/TCP                           
my-release-rasa-x-rasa-x          ClusterIP    10.152.183.154  <none>          5002/TCP                          
my-release-redis-headless         ClusterIP    None            <none>          6379/TCP                          
my-release-redis-master           ClusterIP    10.152.183.114  <none>          6379/TCP                          
```



#### Uninstall a release ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#upgrading-the-deployment))

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Upgrade
h uninstall my-release
```



#### Manage a release

https://helm.sh/docs/intro/using_helm/

```bash
h --help
h ls
h status my-release
```



#### kubectl - manage & monitor nodes, pods, logs, events, etc...

```bash
# To get the details of the nodes 
kubectl get nodes -o wide

# To delete a namespace, will also delete all resources associated with it
kubectl delete namespace my-namespace

# Check the deployments, the pods and the services
k get deployments
k get pods
k get services

# Monitor logs of a single pod
k logs my-release-rasa-x-6fdc69ffd6-4fds7 --follow

# If you see STATUS=CreateContainerConfigError
k describe pod my-release-rasa-x-6fdc69ffd6-4fds7

# To restart a single pod, just scale it down and back up
k get deployments
k scale deployment my-release-rasa-x --replicas=0  # wait until it is gone
k scale deployment my-release-rasa-x --replicas=1

# To get a shell in the container of a pod (if you have only one container per pod)
k exec -it my-release-rasa-x-6fdc69ffd6-4fds7 -- /bin/bash

# To execute a command in a container:
k exec my-release-rasa-x-6fdc69ffd6-4fds7 ls
```



#### stern - monitor logs of multiple pods

```bash
# Use stern to monitor logs of multiple pods
# https://github.com/wercker/stern
wget https://github.com/wercker/stern/releases/download/1.11.0/stern_linux_amd64
chmod +x stern_linux_amd64
mv stern_linux_amd64 stern
./stern -n my-namespace .
```



#### Connect to Rasa X from browser

Rasa X is available on: http://35.166.13.105:8001/

### Maintain disk space

The disk space will keep going up, and these are some typical maintenance steps to check & reduce.

```bash
# check available disk space
df -h /

# find large files on disk
sudo du -cha --max-depth=1 / | grep -E "M|G" | sort -h
```

#### Docker containers & images 

```bash
# clean up docker  (this is safe)
sudo docker system prune
```

#### MicroK8s log files

Kubernetes automatically zips & rotates log files, so they do not blow up the disk.

MicroK8s saves the log files for each pod in the hosts' folder `/var/log/pods/{id}`:

```bash
# check size of microk8s log files larger than 1 Mb
sudo du -cha --max-depth=1 /var/log/pods | grep -E "M|G" | sort -h
> # just remove any large, zipped up log files you no longer want
> # Note that it might be better to configure kubernetes to rotate files differently
```



#### MicroK8s Containers & images

Kubernetes does automatic garbage collection for containers & images as described [here](https://kubernetes.io/docs/concepts/cluster-administration/kubelet-garbage-collection/).

If you do like to check out the containers & images, you can use [microk8s ctr](https://microk8s.io/docs/commands#heading--microk8s-ctr):

```bash
microk8s.ctr images ls
microk8s.ctr containers
```

