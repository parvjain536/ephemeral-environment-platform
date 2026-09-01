# Ephemeral Environment Platform

A containerised FastAPI application deployed on **Amazon EKS**, with infrastructure provisioned using **Terraform** and an automated **GitHub Actions CI/CD pipeline**.

The project demonstrates an end-to-end cloud deployment workflow:

```text
Developer
   │
   │ git push
   ▼
GitHub
   │
   ▼
GitHub Actions
   │
   ├── Run tests
   ├── Build Docker image
   ├── Authenticate to AWS using OIDC
   ├── Push image to Amazon ECR
   ├── Authenticate to Amazon EKS
   ├── Update Kubernetes Deployment
   └── Verify rollout
             │
             ▼
        Amazon EKS
        ┌───────────────┐
        │ Pod           │
        │ FastAPI       │
        │ UID 10001     │
        └───────────────┘
        ┌───────────────┐
        │ Pod           │
        │ FastAPI       │
        │ UID 10001     │
        └───────────────┘
             │
             ▼
       Kubernetes Service
          LoadBalancer
             │
             ▼
        Public HTTP API
```

---

## Features

- FastAPI application served with Uvicorn
- Dockerised application
- Amazon ECR image registry
- Amazon EKS Kubernetes cluster
- Terraform-managed AWS infrastructure
- GitHub Actions CI/CD
- GitHub OIDC authentication to AWS
- No long-lived AWS access keys in GitHub Actions
- Automatic Docker image tagging using the Git commit SHA
- Automatic ECR image push
- Automatic EKS deployment
- Rolling updates with zero unavailable replicas
- Kubernetes liveness and readiness probes
- Two application replicas
- Kubernetes resource requests and limits
- Non-root container execution
- Explicit non-root UID/GID
- RuntimeDefault seccomp profile
- Read-only root filesystem
- Linux capabilities dropped
- Privilege escalation disabled
- ECR image scanning enabled
- Terraform-generated files excluded from Git

---

# Architecture

## AWS architecture

The infrastructure is deployed in the AWS `ap-south-1` region.

```text
                         AWS
                          │
                          ▼
                  ┌───────────────┐
                  │      VPC      │
                  │  10.0.0.0/16  │
                  └───────┬───────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
      Public Subnet 1           Public Subnet 2
       ap-south-1a               ap-south-1b
       10.0.0.0/24               10.0.1.0/24
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
                    Amazon EKS
                 ephemeral-platform
                          │
                    ┌─────┴─────┐
                    │           │
                    ▼           ▼
                  Pod 1       Pod 2
                    │           │
                    └─────┬─────┘
                          │
                          ▼
                 LoadBalancer Service
                          │
                          ▼
                     HTTP :80
```

### Current infrastructure

| Component | Configuration |
|---|---|
| AWS Region | `ap-south-1` |
| VPC CIDR | `10.0.0.0/16` |
| Public subnet 1 | `10.0.0.0/24` |
| Public subnet 2 | `10.0.1.0/24` |
| Availability Zones | `ap-south-1a`, `ap-south-1b` |
| EKS cluster | `ephemeral-platform` |
| Kubernetes version | `1.36` |
| Node group | `ephemeral-platform-nodes` |
| Node instance type | `t3.small` |
| Node desired/min/max | `1 / 1 / 1` |
| ECR repository | `ephemeral-platform` |
| Application replicas | `2` |
| Application port | `8000` |
| Service port | `80` |
| Service type | `LoadBalancer` |

---

# Application

The application is a FastAPI service.

## Endpoints

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

### Root endpoint

```http
GET /
```

Example response:

```json
{
  "message": "Ephemeral Environment Platform",
  "status": "running"
}
```

The `/health` endpoint is also used by Kubernetes for liveness and readiness checks.

---

# Repository Structure

```text
ephemeral-environment-platform/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   └── ...
│
├── docs/
│   └── ...
│
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
│
├── terraform/
│   ├── main.tf
│   ├── network.tf
│   ├── eks.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── tests/
│   └── ...
│
├── .dockerignore
├── .gitignore
├── Dockerfile
└── requirements.txt
```

Terraform state and generated Terraform directories are intentionally excluded from version control.

---

# Prerequisites

Install and configure:

- Git
- Python 3.10
- Docker
- AWS CLI
- Terraform
- kubectl
- An AWS account with sufficient permissions
- A GitHub repository

Verify the tools:

```powershell
git --version
python --version
docker --version
aws --version
terraform version
kubectl version --client
```

Authenticate the AWS CLI:

```powershell
aws configure
```

Verify the active AWS identity:

```powershell
aws sts get-caller-identity
```

---

# Local Development

## Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Install dependencies

```powershell
pip install -r requirements.txt
```

## Run tests

```powershell
python -m pytest
```

## Run the application locally

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Test it:

```powershell
curl.exe http://localhost:8000/health
```

Expected:

```json
{"status":"healthy"}
```

---

# Docker

## Build the image

Example:

```powershell
docker build -t ephemeral-platform:local .
```

## Run locally

```powershell
docker run -d --name ephemeral-test -p 8001:8000 ephemeral-platform:local
```

Test:

```powershell
curl.exe http://localhost:8001/health
```

Expected:

```json
{"status":"healthy"}
```

Check the container user:

```powershell
docker exec ephemeral-test id
```

The production image is configured to run as a non-root user with UID `10001`.

Stop and remove the test container:

```powershell
docker rm -f ephemeral-test
```

---

# Amazon ECR

The application image is stored in:

```text
920810905390.dkr.ecr.ap-south-1.amazonaws.com/ephemeral-platform
```

For manual ECR authentication:

```powershell
aws ecr get-login-password --region ap-south-1 |
docker login --username AWS --password-stdin 920810905390.dkr.ecr.ap-south-1.amazonaws.com
```

Build:

```powershell
docker build -t ephemeral-platform:local .
```

Tag:

```powershell
docker tag ephemeral-platform:local `
  920810905390.dkr.ecr.ap-south-1.amazonaws.com/ephemeral-platform:local
```

Push:

```powershell
docker push `
  920810905390.dkr.ecr.ap-south-1.amazonaws.com/ephemeral-platform:local
```

In normal CI/CD operation, ECR authentication and pushing are handled automatically by GitHub Actions.

---

# Terraform Infrastructure

Terraform provisions the AWS infrastructure required by the platform.

The configuration includes:

- ECR repository
- GitHub OIDC provider
- GitHub Actions IAM role
- ECR permissions for GitHub Actions
- EKS cluster IAM role
- EKS node IAM role
- VPC
- Public subnets
- Internet Gateway
- Public route table
- EKS cluster
- EKS managed node group
- EKS access entry for GitHub Actions
- EKS access policy association

## Initialise Terraform

From the repository root:

```powershell
cd terraform
terraform init
```

## Format

```powershell
terraform fmt
```

## Validate

```powershell
terraform validate
```

## Review changes

```powershell
terraform plan
```

## Apply

```powershell
terraform apply
```

Approve with:

```text
yes
```

## Configure kubectl

After the EKS cluster is created:

```powershell
aws eks update-kubeconfig `
  --region ap-south-1 `
  --name ephemeral-platform
```

Verify:

```powershell
kubectl config current-context
```

Expected context resembles:

```text
arn:aws:eks:ap-south-1:<account-id>:cluster/ephemeral-platform
```

Verify the cluster:

```powershell
aws eks describe-cluster `
  --name ephemeral-platform `
  --region ap-south-1 `
  --query "cluster.status" `
  --output text
```

Expected:

```text
ACTIVE
```

---

# Kubernetes Deployment

The Kubernetes Deployment runs two replicas.

Important deployment properties include:

```yaml
replicas: 2
```

Rolling update strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

This allows a new pod to become available before an old pod is removed.

## Apply the deployment manually

```powershell
kubectl apply -f k8s/deployment.yaml
```

## Apply the service

```powershell
kubectl apply -f k8s/service.yaml
```

## Verify deployment

```powershell
kubectl get deployment ephemeral-platform
```

Expected:

```text
READY   UP-TO-DATE   AVAILABLE
2/2     2            2
```

## Verify pods

```powershell
kubectl get pods
```

## Verify rollout

```powershell
kubectl rollout status deployment/ephemeral-platform
```

Expected:

```text
deployment "ephemeral-platform" successfully rolled out
```

---

# Kubernetes Security

The deployment is intentionally hardened.

## Non-root execution

The application runs using UID/GID `10001`.

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
```

This prevents the application container from running as root.

Verify:

```powershell
kubectl exec deployment/ephemeral-platform -- id
```

Expected:

```text
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

## Seccomp

The deployment uses:

```yaml
seccompProfile:
  type: RuntimeDefault
```

This applies the container runtime's default seccomp restrictions.

## Read-only root filesystem

```yaml
readOnlyRootFilesystem: true
```

This reduces the ability of the application process to modify the container filesystem.

## Privilege escalation disabled

```yaml
allowPrivilegeEscalation: false
```

## Linux capabilities dropped

```yaml
capabilities:
  drop:
    - ALL
```

## Resource limits

Each container has:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

These provide Kubernetes scheduling requirements and upper resource limits.

---

# Kubernetes Health Checks

The application exposes:

```text
GET /health
```

Kubernetes uses the endpoint for both liveness and readiness.

Example:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000

readinessProbe:
  httpGet:
    path: /health
    port: 8000
```

Verify:

```powershell
kubectl describe deployment ephemeral-platform
```

---

# Load Balancer

The Kubernetes service uses:

```yaml
type: LoadBalancer
```

Check it:

```powershell
kubectl get service ephemeral-platform
```

The `EXTERNAL-IP` column provides the AWS load balancer hostname.

Example:

```text
ephemeral-platform   LoadBalancer   ...   <load-balancer-hostname>   80:xxxxx/TCP
```

Test the application:

```powershell
curl.exe http://<LOAD-BALANCER-HOSTNAME>/health
```

Expected:

```json
{"status":"healthy"}
```

Test the root endpoint:

```powershell
curl.exe http://<LOAD-BALANCER-HOSTNAME>/
```

Expected:

```json
{"message":"Ephemeral Environment Platform","status":"running"}
```

---

# CI/CD

The GitHub Actions workflow is located at:

```text
.github/workflows/ci.yml
```

The workflow runs on pushes and pull requests targeting `main`.

## Pipeline

```text
Push / Pull Request
        │
        ▼
Checkout
        │
        ▼
Set up Python 3.10
        │
        ▼
Install dependencies
        │
        ▼
Run pytest
        │
        ├── Pull Request → stop after tests
        │
        ▼
Configure AWS credentials
        │
        ▼
Login to ECR
        │
        ▼
Docker build
        │
        ▼
Push image to ECR
        │
        ▼
Configure kubectl
        │
        ▼
Update EKS Deployment
        │
        ▼
Wait for rollout
        │
        ▼
Verify deployment and pods
```

Pushes to `main` use the Git commit SHA as the Docker image tag.

Example:

```text
ephemeral-platform:<git-sha>
```

This provides immutable, traceable deployment versions.

---

# GitHub OIDC Authentication

The CI/CD pipeline does not require storing long-lived AWS access keys in GitHub secrets.

GitHub Actions obtains an OIDC identity token and assumes the dedicated AWS IAM role:

```text
ephemeral-platform-github-actions
```

The trust policy restricts role assumption to the intended GitHub repository and branch.

The workflow uses:

```yaml
permissions:
  id-token: write
  contents: read
```

and:

```yaml
uses: aws-actions/configure-aws-credentials@v5
```

This provides short-lived AWS credentials during the workflow.

---

# IAM Permissions

The GitHub Actions IAM role has permissions required for:

- ECR authentication
- ECR layer upload
- ECR image publishing
- EKS deployment access

The ECR permissions include:

```text
ecr:GetAuthorizationToken
ecr:BatchCheckLayerAvailability
ecr:CompleteLayerUpload
ecr:InitiateLayerUpload
ecr:PutImage
ecr:UploadLayerPart
```

The EKS access configuration grants the GitHub Actions role cluster-level EKS access required by the deployment workflow.

---

# Deployment Verification

After a CI/CD run, verify the deployed image:

```powershell
kubectl get deployment ephemeral-platform `
  -o jsonpath="{.spec.template.spec.containers[0].image}"
```

The result should contain the Git commit SHA used by the workflow.

Verify rollout:

```powershell
kubectl rollout status deployment/ephemeral-platform
```

Verify pods:

```powershell
kubectl get pods
```

Verify the service:

```powershell
kubectl get service ephemeral-platform
```

Verify endpoints:

```powershell
kubectl get endpointslices
```

Verify the running user:

```powershell
kubectl exec deployment/ephemeral-platform -- id
```

---

# Useful Kubernetes Commands

## Deployment

```powershell
kubectl get deployment ephemeral-platform
kubectl describe deployment ephemeral-platform
kubectl rollout status deployment/ephemeral-platform
kubectl rollout history deployment/ephemeral-platform
```

## Pods

```powershell
kubectl get pods
kubectl get pods -o wide
kubectl describe pods
```

## Service

```powershell
kubectl get service ephemeral-platform
kubectl describe service ephemeral-platform
kubectl get endpointslices
```

## Current image

```powershell
kubectl get deployment ephemeral-platform `
  -o jsonpath="{.spec.template.spec.containers[0].image}"
```

## Container security context

```powershell
kubectl get deployment ephemeral-platform `
  -o jsonpath="{.spec.template.spec.securityContext}"
```

```powershell
kubectl get deployment ephemeral-platform `
  -o jsonpath="{.spec.template.spec.containers[0].securityContext}"
```

---

# Useful AWS Commands

## Current AWS identity

```powershell
aws sts get-caller-identity
```

## ECR repository

```powershell
aws ecr describe-repositories `
  --repository-names ephemeral-platform `
  --region ap-south-1
```

## ECR images

```powershell
aws ecr list-images `
  --repository-name ephemeral-platform `
  --region ap-south-1
```

## EKS status

```powershell
aws eks describe-cluster `
  --name ephemeral-platform `
  --region ap-south-1 `
  --query "cluster.status" `
  --output text
```

## EKS node groups

```powershell
aws eks list-nodegroups `
  --cluster-name ephemeral-platform `
  --region ap-south-1
```

---

# Troubleshooting

## Terraform says "No configuration files"

Terraform commands must be executed from the directory containing the `.tf` files.

```powershell
cd E:\Dev\ephemeral-environment-platform\terraform
terraform plan
```

Do not run Terraform from the repository root unless configuration files are present there.

---

## Kubernetes cannot authenticate

Refresh the kubeconfig:

```powershell
aws eks update-kubeconfig `
  --region ap-south-1 `
  --name ephemeral-platform
```

Then:

```powershell
kubectl get nodes
```

---

## Deployment rollout is stuck

Check:

```powershell
kubectl get pods
kubectl describe pods
kubectl describe deployment ephemeral-platform
kubectl get rs
```

Look at pod events for scheduling, image pull, readiness, or security-context failures.

---

## Image pull failure

Verify the image exists:

```powershell
aws ecr list-images `
  --repository-name ephemeral-platform `
  --region ap-south-1
```

Verify the deployment image:

```powershell
kubectl get deployment ephemeral-platform `
  -o jsonpath="{.spec.template.spec.containers[0].image}"
```

---

## Application health check fails

Check logs:

```powershell
kubectl logs deployment/ephemeral-platform
```

Check the pod directly:

```powershell
kubectl exec deployment/ephemeral-platform -- id
```

Check the service endpoints:

```powershell
kubectl get endpointslices
```

---

# Security Considerations

The project intentionally applies several container and Kubernetes security controls:

1. The application runs as a non-root user.
2. The UID/GID is explicitly set to `10001`.
3. Privilege escalation is disabled.
4. All Linux capabilities are dropped.
5. The root filesystem is read-only.
6. RuntimeDefault seccomp is enabled.
7. Kubernetes health probes are configured.
8. CPU and memory resources are bounded.
9. ECR image scanning is enabled.
10. GitHub Actions uses OIDC instead of long-lived AWS credentials.
11. Terraform state and generated Terraform directories are excluded from Git.
12. Docker and Kubernetes deployment images are traceable using Git commit SHAs.

---

# Reproducible Deployment

A normal deployment to `main` is triggered with:

```powershell
git add .
git commit -m "your change"
git push origin main
```

GitHub Actions then performs the build and deployment automatically.

A successful run should result in:

```text
Tests
  ✓

Docker build
  ✓

ECR push
  ✓

AWS OIDC
  ✓

EKS authentication
  ✓

Deployment
  ✓

Rollout
  ✓
```

---

# Infrastructure Cleanup

If the environment is no longer required, Terraform can remove the AWS resources it manages.

From the Terraform directory:

```powershell
cd terraform
terraform plan -destroy
```

Review the destruction plan carefully.

Then:

```powershell
terraform destroy
```

Approve with:

```text
yes
```

**Do not run `terraform destroy` on a shared or production environment without confirming that the resources are safe to remove.**

---

# Current Validation Status

The implementation has been validated end-to-end.

Verified:

- Terraform configuration validates successfully
- AWS infrastructure is provisioned
- EKS cluster reaches `ACTIVE`
- EKS node reaches `Ready`
- Kubernetes deployment reaches `2/2` available replicas
- Pods reach `Running`
- Container runs as UID `10001`
- `runAsNonRoot` is enabled
- `RuntimeDefault` seccomp is enabled
- `readOnlyRootFilesystem` is enabled
- `allowPrivilegeEscalation` is disabled
- All Linux capabilities are dropped
- Kubernetes rolling update succeeds
- LoadBalancer is provisioned
- `/health` returns a healthy response
- `/` returns the application response
- GitHub Actions CI/CD completes successfully
- Docker images are pushed to ECR
- EKS deployments are updated automatically from CI/CD
- Git working tree is clean
- Terraform generated files are ignored by Git

---

# Technology Stack

- **Application:** Python / FastAPI
- **Application server:** Uvicorn
- **Container:** Docker
- **Registry:** Amazon ECR
- **Orchestration:** Kubernetes / Amazon EKS
- **Infrastructure as Code:** Terraform
- **Cloud:** AWS
- **CI/CD:** GitHub Actions
- **Authentication:** GitHub OIDC + AWS IAM
- **Testing:** pytest

---

# Project Outcome

This project demonstrates a complete cloud-native deployment lifecycle:

```text
Application
    ↓
Containerisation
    ↓
Container Registry
    ↓
Infrastructure as Code
    ↓
Managed Kubernetes
    ↓
Secure Workload
    ↓
Load Balancing
    ↓
Automated CI/CD
    ↓
Rolling Deployment
    ↓
Health Verification
```

The result is a reproducible FastAPI deployment on AWS EKS with automated image delivery, automated Kubernetes deployment, OIDC-based AWS authentication, rolling updates, health checks, and container security hardening.
