# 🚀 FastAPI GitOps CI/CD Pipeline

A production-grade CI/CD pipeline implementing GitOps principles to deploy a FastAPI microservice across multiple Kubernetes environments (Dev, Staging, Prod).

![Jenkins](https://img.shields.io/badge/Jenkins-CI/CD-D24939)
![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Kind-326CE5)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)

<img src="./images/Python.svg" width="80" height="80" alt="Python"/> <img src="./images/FastAPI.svg" width="80" height="80" alt="FastAPI"/>
<img src="./images/Docker.svg" width="80" height="80" alt="Docker"/>
<img src="./images/Kubernetes.svg" width="80" height="80" alt="Kubernetes"/>
<img src="./images/Jenkins.svg" width="80" height="80" alt="Jenkins"/>
<img src="./images/Helm.svg" width="80" height="80" alt="Helm"/>
<img src="./images/ArgoCD.svg" width="80" height="80" alt="ArgoCD"/>

## 🛠️ Tech Stack

- Application: FastAPI, Python 3.12

- CI/CD Engine: Jenkins (Pipeline-as-Code / Groovy DSL)

- GitOps Controller: ArgoCD

- Containerization: Docker

- Orchestration: Kubernetes (Kind Cluster)

- Testing: Pytest

## ✅ Prerequisites

- Docker installed on EC2
- Kind installed [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- helm installed [helm](https://helm.sh/docs/intro/install)
- kubectl configured
- ArgoCD installed in cluster
- Jenkins running as a Docker container on the Kind network

## 📁 Repository Structure

```
Main branch
fastapi-gitops-pipeline/
├── app
│   ├── main.py
│   ├── requirements.txt
│   └── test_main.py
├── argocd-apps
│   ├── dev-app.yml
│   ├── prod-app.yml
│   └── stage-app.yml
├── Dockerfile
├── Jenkinsfile
├── README.md
└── scripts
    └── rollback.sh

Gitops Branch
└── k8s
    ├── dev
    │   ├── deployment.yml
    │   ├── namespace.yml
    │   └── service.yml
    ├── prod
    │   ├── deployment.yml
    │   ├── namespace.yml
    │   └── service.yml
    └── staging
        ├── deployment.yml
        ├── namespace.yml
        └── service.yml
```

## 🏗️ Pipeline Architecture

The pipeline follows a Staged Promotion strategy, ensuring that only verified, healthy code reaches the Production environment.

### 1. Continuous Integration (CI)

- Testing: Runs pytest on the application code within a virtual environment.

- Build: Generates a Docker image tagged with the unique ${BUILD_NUMBER}.

- Push: Pushes the immutable image to Docker Hub and loads it into the local Kind cluster.

### 2. Continuous Deployment (CD) & GitOps

- Environment Isolation: Manifests are managed in environment-specific directories (k8s/dev, k8s/staging, k8s/prod).

- Automated Promotion: Jenkins updates the image tag in Git manifests and pushes to the gitops branch.

- ArgoCD Sync: ArgoCD detects the Git change and synchronizes the cluster state automatically.

### 3. Fail-Safe & Rollback Logic

- Health Checks: Every deployment is followed by a kubectl rollout status check.

- Circuit Breaker: If a deployment fails in Dev, the pipeline stops immediately, protecting Staging and Prod.

- Auto-Rollback: Upon failure, the pipeline automatically reverts the Git manifest to the previous stable version.

### 4. Human-in-the-Loop (Production Gate)

- A Manual Approval Stage with a 24-hour timeout is implemented before the Production deployment, allowing for final manual verification of the Staging environment.

## 🚦 How to Run

### I have build this project on ec2 instance so i'll be showing steps how to set in ec2. Make sure you have already running a ec2 instance. I have used m71-flex-large instance as i was facing issue to set my repo with argocd server and it was keep getting failed for most of the time.

### 1. Clone the Repository

```bash
git clone https://github.com/amandev-x/fastapi-gitops-pipeline.git
cd fastapi-gitops-pipeline

```

### 2. Create a Kind Cluster

```bash
kind create cluster --name gitops --config gitops.yml
```

### 3. Add Argo helm repo and create argocd namespace and use Helm to install ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### 4. Create argocd namespace and use Helm to install ArgoCD

```bash
kubectl create namespace argocd
helm install argocd argo/argo-cd -n argocd
```

### 5. Verify Installation

```bash
kubectl get all -n argocd
kubectl get svc -n argocd
```

### 6. Wait for ArgoCD to be ready

``` bash
kubectl wait --for=condition=available deployment -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

### 6. Access the ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8081:443 --address 0.0.0.0
```

### 7. Create Namespaces

```bash
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace prod
```

### 8. Connect repository to the ArgoCD

``` bash
1. Go the ArgoCD UI page: https://<EC2-public-ip>:8081(Make sure that you have created an inbound rule for this port)
2. Click on the setting tab
3. Click on the repositories tab
4. Click on the Add Repository button
5. Click to HTTP/HTTPs connection
6. Select project default
7. Enter the project name(optional)
8. Enter the repository URL: https://github.com/amandev-x/fastapi-gitops-pipeline.git
9. Click on the connect button and the repository will be connected
```

### 9. Create an copy of the ./kube/config file and change its server address

```bash
cp $HOME/.kube/config ~/.kube/config-jenkins
sed -i 's/127.0.0.1/<control-node-name>:6443/g' ~/.kube/config-jenkins
```

### 10. Create a Jenkins Docker container

We are going to give the Jenkins container access to the host docker socket, so that it can build and push images to the Docker Hub. Also we are going to use kind network so both jenkins and kind cluster can be on same network. And finally we are going the .kube/config file and kubectl binary to Jenkins container so it can run kubectl commands inside the container.
To make jenkins container write to the docker socket we need to find the GID of the ec2 host.

```bash
stat -c '%g' /var/run/docker.sock # Find the GID of the docker socket
```

Then we need to add the GID to the Jenkins container so it can write to the docker socket.
Use the GID to the --group-add flag of the docker run command.

```bash
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 --network kind \
-v jenkins_home:/var/jenkins_home -v /usr/local/bin/kind:/usr/bin/kind \
-v /usr/local/bin/kubectl:/usr/local/bin/kubectl \
-v $HOME/.kube/config-jenkins:/var/jenkins_home/.kube/config-jenkins \
-v /var/run/docker.sock:/var/run/docker.sock \
--group-add $(stat -c '%g' /var/run/docker.sock) jenkins/jenkins:lts 
```

### 11. Exec into the jenkins container and install the following packages

```bash
docker exec -it -u root jenkins bash
apt-get update
apt-get install -y docker.io python3 python3-pip python3-venv vim
```

### 12. Configure Jenkins Credentials

Add the following credentials in Jenkins (`Manage Jenkins → Credentials`):

| ID | Type | Description |
|----|------|-------------|
| `github-credentials` | Username & Password | GitHub username + PAT |
| `dockerhub-credentials` | Username & Password | Docker Hub username + password |

### 13. Create Jenkins Pipeline Job

Go to Jenkins → **New Item** → **Pipeline**

- Under **Pipeline**, set definition to **Pipeline script from SCM**
- Set SCM to **Git**, repo URL to this repository, branch to `main`
- Jenkins will automatically detect the `Jenkinsfile`
- Change the docker image name to yours dockerusername/fastapi-gitops-pipeline
- Click **Create**

### 14. Trigger the Pipeline

Click on the **Build Now** button
Pipeline will automatically trigger and deploy through Dev → Staging → Prod with a manual approval gate before Prod.

## 🔄 Pipeline Flow

```
Code Push → Pytest → Docker Build → Load to Kind
                                          ↓
                                      Deploy Dev
                                          ↓
                                      Health Check ❌ → Auto Rollback  → Pipeline Stops
                                          ↓ ✅
                                      Push to DockerHub (:IMAGE_TAG only, not :latest)
                                          ↓ ✅
                                      Deploy Staging
                                          ↓
                                      Health Check ❌ → Auto Rollback  → Pipeline Stops
                                          ↓ ✅
                                      Manual Approval (24h timeout)
                                          ↓ ✅
                                      Deploy Prod
                                          ↓
                                      Health Check ❌ → Auto Rollback → Pipeline Stops
                                          ↓ ✅
                                      Push :latest to DockerHub (fully verified)
                                          ↓
                                      Save .last_stable_tag to gitops branch ✅
```

## ⏪ Rollback Strategy

### If a deployment fails health checks, Jenkins automatically:

1. Reads .last_stable_tag file from the gitops branch — this always points to the last fully verified build that passed all environments
2. Reverts the failed environment's manifest image tag back to the last stable tag
3. Commits and pushes the reverted manifest to the gitops branch with [skip ci] to prevent CI loop
4. ArgoCD detects the change and automatically syncs the stable version back
5. Pipeline stops immediately — protecting the next environments from receiving a broken image

### Sequential Crash Protection

```
Build #5 → ✅ All envs pass  → .last_stable_tag = 5
Build #6 → ❌ Dev fails      → rollback to 5 ✅
Build #7 → ❌ Dev fails      → rollback to 5 ✅ (not 6 which was also broken)
Build #8 → ✅ All envs pass  → .last_stable_tag = 8
Build #9 → ❌ Staging fails  → rollback staging to 8 ✅
```

## 📸 Screenshots

### Pipeline Success

![SuccessPipeline](./images/Screenshot%20from%202026-03-06%2010-42-04.png)

### Pipeline Failure

![FailurePipeline](./images/Screenshot%20from%202026-03-06%2010-42-38.png)

## License

[MIT](https://choosealicense.com/licenses/mit/)