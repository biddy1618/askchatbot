# Instructions to build & deploy the chatbot

### Connect to the knowledge base instance

To connect to the knowledge base instance, configure the following in 
`<project-root>/credentials_knowledge_base.yml`:

- `kb_instance` - This is just the instance address, you don't need the leading https.
- `kb_user` - The username of the service account the action code will use to query the knowledge base.
- `kb_pw` - The password of the service account the action code will use to query the knowledge base.
- `localmode` -  When set to `true` (default in the code),  the action server will **not** send an actual query to the `kb_instance`. 

# Build docker image of action server

For now, we will build & push the docker image of the action server manually. You can run the commands locally or on the EC2 instance.

A Dockerfile is included in the project-root folder.

### Build the docker image

```bash
to describe...
```

### Test locally

```bash
to describe...
```

### Push the docker image

```bash
to describe...
```





# Deploy to k3s on EC2 instance

### Install k3s & helm ([docs](https://rancher.com/docs/k3s/latest/en/quick-start/))

```bash
# install k3s cluster
curl -sfL https://get.k3s.io | sh -

# install helm
sudo snap install helm --classic

##############################
# Add this to your ~/.bashrc #
##############################
# Make k3s cluster accessible
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
sudo chmod +r /etc/rancher/k3s/k3s.yaml

# set aliases for using kubectl in a namespace
alias k="kubectl --namespace ipm-namespace"

# set aliases for using helm  in a namespace
alias h="helm --namespace ipm-namespace"

####################################
# then, make these aliases available
source ~/.bashrc
```



### k3s systemd service

The k3s installer creates a `k3s systemd service` which can be used for `stop`, `start`, `restart` and verify the `status` of the k3s server running Kubernetes.

```bash
# https://askubuntu.com/questions/19320/how-to-enable-or-disable-services

# temporarily stop/start/restart
sudo systemctl status k3s
sudo systemctl stop k3s
sudo systemctl start k3s
sudo systemctl restart k3s

# enable/disable startup on reboot
sudo systemctl is-enabled k3s
sudo systemctl enable k3s
sudo systemctl disable k3s

# To get the details of the nodes 
kubectl get nodes -o wide

# To uninstall & remove k3s
sudo /usr/local/bin/k3s-uninstall.sh
sudo rm -rf /var/lib/rancher
```



### Rasa X Helm Install

[Rasa X docs on using helm](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/)

[Rasa X Helm Chart repository](https://github.com/rasahq/rasa-x-helm)

#### Clone the git repo

The git repo is temporarily stored in github. I added a temporary deploy key to the repo to be able to use git with ssh from the command line. I could then clone the github repo with:

```bash
mkdir ~/repos
cd ~/repos
git clone git@github.com:ArjaanBuijkLLC/ipm-demo.git
```

#### Create a secret deployment directory with template `values.yml`

The data in this folder contain passwords related to the deployment, so we name it `secret` and there is no chance this is pushed into the git repo by accident because of the `.gitignore` .

```bash
# make & enter the deployment work directory
cd ~/repos/deploy
mkdir secret
cd ~/repos/deploy/secret

# edit a values.yml in this folder & deploy from this folder...
```



#### Create the Kubernetes name-space

```bash
# Verify all is in place
kubectl version --short --client
kubectl version --short
helm version

# To start fresh, first delete the namespace
kubectl delete namespace ipm-namespace

# Create the namespace
kubectl create namespace ipm-namespace
```

#### `values.yml` ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#quick-install))

Edit the template `values.yml` as  shown:

- It is recommended to use debugMode, so the log files contain more information.
- Expose nginx on default HTTP port 8000
- Make sure to replace every `<safe credential>` with a different alphanumeric string

```bash
# use Debug or not
debugMode: "true"
# nginx specific settings
nginx:
  service:
    # port is the port which the nginx service exposes for HTTP connections
    port: 8000
# rasax specific settings
rasax:
    # initialUser is the user which is created upon the initial start of Rasa X
    initialUser:
        # password for the Rasa X user
        password: "<safe credential>"
    # passwordSalt Rasa X uses to salt the user passwords
    passwordSalt: "<safe credential>"
    # token Rasa X accepts as authentication token from other Rasa services
    token: "<safe credential>"
    # jwtSecret which is used to sign the jwtTokens of the users
    jwtSecret: "<safe credential>"
    tag: "0.28.5"
# rasa: Settings common for all Rasa containers
rasa:
    # token Rasa accepts as authentication token from other Rasa services
    token: "<safe credential>"
    tag: "1.10.1-full"
# RabbitMQ specific settings
rabbitmq:
    # rabbitmq settings of the subchart
    rabbitmq:
        # password which is used for the authentication
        password: "<safe credential>"
# global settings of the used subcharts
global:
    # postgresql: global settings of the postgresql subchart
    postgresql:
        # postgresqlPassword is the password which is used when the postgresqlUsername equals "postgres"
        postgresqlPassword: "<safe credential>"
    # redis: global settings of the postgresql subchart
    redis:
        # password to use in case there no external secret was provided
        password: "<safe credential>"

```



#### Add Image Pull Secrets for Private Registries ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#adding-image-pull-secrets-for-private-registries))

TO BE UPDATED FOR GITLAB CONTAINER REGISTRY

In the Kubernetes namespace, create a [secret](https://kubernetes.io/docs/concepts/configuration/secret/) for the private registry of the custom containers.

```bash
###################################################################################
# Create a 'docker-registry' secret in the cluster, for use with a Docker registry
# -> to give access to Eduworks' private container registry
# -> see: https://kubernetes.io/docs/concepts/configuration/secret/
vi eduworks-cr-auth.json
-> Get content from sample VM

k create secret docker-registry eduworks-cr-pull-secret \
    --docker-server=<HOST, like gcr.io> \
    --docker-username=_json_key \
    --docker-password="$(cat eduworks-cr-auth.json)"
k get secrets
k get secret eduworks-cr-pull-secret --output=yaml
k get secret eduworks-cr-pull-secret --output="jsonpath={.data.\.dockerconfigjson}" | base64 --decode
#

# add eduworks-cr-pull-secret to values.yml 
vi values.yml
images:
    imagePullSecrets:
    - name: "eduworks-cr-pull-secret"
```



#### Add Custom Action Server ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#adding-a-custom-action-server))

```bash
vi values.yml
# app (custom action server) specific settings
app:
    # name of the custom action server image to use
    name: "gcr.io/eduworks-277711/ipm-demo"
    # tag refers to the custom action server image tag
    tag: "0.0.1"
```



#### Configure Rasa Open Source Channels ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#configuring-rasa-open-source-channels))

```bash
vi values.yml
...
```



#### Deploy  ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#quick-install))

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Deploy
h install ipm-release --values values.yml rasa-x/rasa-x

# Optional: Check how the kubectl generated objects yaml looks like
# -> Not using it, just for educational purposes
h template --values values.yml ipm-release rasa-x/rasa-x > rasa-x-deployment.yml
```



#### Check deployment progress

Note that it takes a while before all the pods are running. Especially the r`asa-production` pod takes awhile to start up due to the large image file to be download. 

The following commands are very useful to monitor the deployment progress.

```bash
k get pods
k describe pods ipm-release-rasa-production-65584db86c-dgflc
```



##### Check health via curl on EC2

```bash
curl http://localhost:8000/api/version
```



##### OPTIONAL, BUT NOT DONE --- JUST OPENED PORT 8000... Redirect port 80 to port 8000

```bash
# TODO -- redirect port 80 to port 8000

# https://coderwall.com/p/plejka/forward-port-80-to-port-3000
sudo iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8000
```



#### Upgrade/Modify a release ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#upgrading-the-deployment))

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Upgrade
h upgrade ipm-release --values values.yml --reuse-values rasa-x/rasa-x
```



#### Uninstall a release ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#upgrading-the-deployment))

```bash
# Add the repository which contains the Rasa X Helm chart
helm repo add rasa-x https://rasahq.github.io/rasa-x-helm
helm repo update

# Upgrade
h uninstall ipm-release
```



#### Manage a release

https://helm.sh/docs/intro/using_helm/

```bash
h --help
h ls
h status ipm-release
```



#### stern - monitor logs of multiple pods

```bash
# Use stern to monitor logs of multiple pods
# https://github.com/wercker/stern
wget https://github.com/wercker/stern/releases/download/1.11.0/stern_linux_amd64
chmod +x stern_linux_amd64
mv stern_linux_amd64 stern
./stern -n ipm-namespace .

./stern --help
./stern <---some-name-query---> -n ipm-namespace .

```





### kubectl - manage & monitor nodes, pods, logs, events, etc...

```bash
# To get the details of the nodes 
kubectl get nodes -o wide

# To delete a namespace, will also delete all resources associated with it
kubectl delete namespace ipm-namespace

# Check the deployments, the pods and the services
k get deployments
k get pods
k get services

# Monitor logs of a single pod
k logs ipm-release-rasa-x-6fdc69ffd6-4fds7 -f

# If you see STATUS=CreateContainerConfigError
k describe pod ipm-release-rasa-x-6fdc69ffd6-4fds7

# To restart a single pod, just scale the deployment down and back up
k get deployments
k scale deployment ipm-release-app --replicas=0  # wait until it is cone
k scale deployment ipm-release-app --replicas=1

# To get a shell in the container of a pod (if you have only one container per pod)
k exec -it ipm-release-rasa-x-6fdc69ffd6-4fds7 -- /bin/bash

# To execute a command in a container:
k exec ipm-release-rasa-x-6fdc69ffd6-4fds7 ls
```



### Modify password of Rasa X user ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/openshift-kubernetes/#create-update-rasa-x-users))

```bash
# get shell inside the rasa-x container, and run a script
ki get pod -l app.kubernetes.io/component=rasa-x
ki exec -it <name of the Rasa X pod> bash
> python scripts/manage_users.py create --update me <password> admin

```



### Connect to Rasa X from browser

```bash
# Get external IP 

# Local install on ubuntu
# - just use IP = localhost
# or
# - get the EXTERNAL IP of the LoadBalancer server
k get services

# For VM at AWS ==> get it from AWS Console for the VM Instance

# Then, connect at
http://<IP>:8100
```



### Connect Rasa X to gitlab ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/integrated-version-control/))

The bot is temporarily stored in https://github.com/ArjaanBuijkLLC/ipm-demo

From Rasa X, connect to the git repository as described in the docs.

### Optional - Kubernetes Dashboard ([docs](https://rancher.com/docs/k3s/latest/en/installation/kube-dashboard/))

```bash
# Deploying the Kubernetes Dashboard
GITHUB_URL=https://github.com/kubernetes/dashboard/releases
VERSION_KUBE_DASHBOARD=$(curl -w '%{url_effective}' -I -L -s -S ${GITHUB_URL}/latest -o /dev/null | sed -e 's|.*/||')
sudo k3s kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/${VERSION_KUBE_DASHBOARD}/aio/deploy/recommended.yaml

# vi dashboard.admin-user.yml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
  
# vi dashboard.admin-user-role.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
  
# Deploy the admin-user configuration:
kubectl create -f dashboard.admin-user.yml -f dashboard.admin-user-role.yml

# Obtain the Bearer Token
kubectl -n kubernetes-dashboard describe secret admin-user-token | grep ^token

# To access the Dashboard you must create a secure channel to your Kubernetes cluster:
kubectl proxy
Starting to serve on 127.0.0.1:8001

# The Dashboard is now accessible at:
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
Sign In with the admin-user Bearer Token

# Advanced: Remote Access to the Dashboard --> See docs

# Upgrading the Dashboard
kubectl delete ns kubernetes-dashboard
GITHUB_URL=https://github.com/kubernetes/dashboard/releases
VERSION_KUBE_DASHBOARD=$(curl -w '%{url_effective}' -I -L -s -S ${GITHUB_URL}/latest -o /dev/null | sed -e 's|.*/||')
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/${VERSION_KUBE_DASHBOARD}/aio/deploy/recommended.yaml -f dashboard.admin-user.yml -f dashboard.admin-user-role.yml

# Deleting the Dashboard and admin-user configuration, just delete the namespace
kubectl delete ns kubernetes-dashboard
```
