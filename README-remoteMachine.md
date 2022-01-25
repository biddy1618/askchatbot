# Remote desktop

* Service - Amazon EC2
* Instance - [t4g.xlarge](https://aws.amazon.com/ec2/instance-types/t2/)
* [Price](https://calculator.aws/#/createCalculator/EC2) - 108.11 USD monthly

Instance control dashboard available at https://console.aws.amazon.com/

## Networking

TCP connections set up for all complete port range.

Download __aws.pen__ key-pair (RSA) for access and identity.

Connect through SSH (locate key-pair - `aws.pen`) using hostname generated after restart of instance:
```
ssh -i "aws.pem" ubuntu@ec2-18-203-253-240.eu-west-1.compute.amazonaws.com
```

### VSCode SSH remote

1) Install __Remote SSH__ extension.
2) Set up config file for remote SSH connect as follows and change the hostname accordingly - __EC2 instances generate new host name every time restart__:
```
Host aws-ec2-test
    HostName ec2-34-241-180-151.eu-west-1.compute.amazonaws.com
    User ubuntu
    IdentityFile ~/Toptal/Eduworks/aws.pem

Host aws-ec2-dev
    HostName ec2-18-203-253-240.eu-west-1.compute.amazonaws.com
    User ubuntu
    IdentityFile ~/Toptal/Eduworks/aws.pem
```
3) Use port forwarding to access the services using Remote SSH extension to access remote host's services.

## Remote host setup

Update system: `sudo apt get update`.

### Git setup
1) Add (copy from local machine) or generate new (`ssh-keygen -t rsa -C aws`) __SSH key__ to __~/.ssh/__ folder.
2) Add SSH key to GitLab.
3) Generate (or copy) the token for GitLab access.
4) Copy the repo using HTTPS - `git clone https://git.eduworks.us/ask-extension/askchatbot.git`
    * Enter the username as __dauren.baitursyn__.
    * The password is the token that was generated (or copied).
    * One can store the credentials using following:
    ```
    # this will store your credentials "forever"
    git config --global credential.helper store
    ```

### Docker set up

Run the following to check for updates and installing 3rd packages:
```
sudo apt remove docker docker-engine docker.io containerd runc
sudo apt update
sudo apt install ca-certificates curl gnupg lsb-release
```

Run the following to add official Docker GPG key and setting up the stable repository:
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install docker engine:
```
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

Make `docker` command `sudo`:
```
sudo groupadd docker
sudo usermod -aG docker $USER
```

Reboot the instance.

Test the installation:
```
docker --version
```

Source at official Docker page - [source](https://docs.docker.com/engine/install/ubuntu/).

### Docker compose set up

Run the following command (replace the uname with [last version](https://github.com/docker/compose/releases)):
```
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
```

Test the installation:
```
docker compose version
```

More info can be found at [here](https://docs.docker.com/compose/cli-command/#installing-compose-v2).

### Portrainer for container management

Create volume for portrainer:
```
cd ~/
docker volume create portainer_data
```

Run the container and forward the ports (8000 for UI):
```
docker run -d  -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer
```

The 8000 port is only required if you plan to use the Edge compute features with Edge agents.

More can be found in [here](https://docs.portainer.io/v/ce-2.9/start/install/server/docker/linux).

### Setting up Rasa locally using miniconda

Install miniconda:
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
```

Verify it works:
```
(base) > conda --version
```

Create conda environment and install dependencies for local development (use legacy dependency resolver for pip, otherwise it might take time):
```
conda create --name askchatbot python=3.7
conda activate askchatbot
pip install --use-deprecated=legacy-resolver -r requirements-dev.txt
```

Once the libraries are installed, try running the pip install command once again.
```
pip install -r requirements-dev.txt
```

It is __recommended to install the libraries explicitly stating versions and in order__, if you face some dependency issues.
```
pip install rasa=1.10.10 rasa-sdk=1.10.0 elasticsearch==7.7.0
pip install infelct pandas pillow
```

### Installing Rasa X locally using miniconda

Activate the conda environment where the Rasa was installed then run the following (Rasa 1.10.* is compatible with Rasa-X 0.32.0):
```
pip install rasa-x==0.32.0 --extra-index-url https://pypi.rasa.com/simple
```

# Host address

Use the following address to access the gitlab - `git@160.1.7.191:ask-extension/askchatbot.git`