# SpendWise AI — AWS Deployment Guide

This guide covers Step 32 and Step 33 of Phase 6: Finalizing the Cloud environment.

## Step 32: S3 Bucket CORS Configuration
Because the frontend (running on React/Nginx) will securely upload receipts directly to your AWS S3 bucket using a Pre-Signed URL, the bucket must allow Cross-Origin Resource Sharing (CORS).

**Run the following AWS CLI command to configure CORS:**

```bash
# First, create a file named cors.json
cat <<EOF > cors.json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["PUT", "POST", "GET"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
EOF

# Apply the CORS configuration to your bucket
aws s3api put-bucket-cors --bucket spendwise-receipts-default --cors-configuration file://cors.json
```
*(Replace `spendwise-receipts-default` with your actual bucket name. In production, change `AllowedOrigins` from `*` to your exact domain name).*

## Step 33: AWS Deployment (EC2 / ECS / AppRunner)

To deploy this multi-container application to AWS, you have three primary options:

### Option A: EC2 + Docker Compose (Easiest)
1. Provision a single EC2 Instance (e.g., `t3.medium`).
2. SSH into the instance and install Docker & Docker Compose.
3. Clone this repository.
4. Populate your `.env` file with secure production passwords.
5. Run `docker compose up -d --build`.

### Option B: AWS ECS (Elastic Container Service) using Fargate (Enterprise Grade)
1. Push your 3 custom Docker images (`frontend`, `backend`, `ai-service`) to Amazon ECR (Elastic Container Registry):
    ```bash
    aws ecr create-repository --repository-name spendwise-backend
    docker build -t spendwise-backend ./backend
    docker tag spendwise-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/spendwise-backend
    docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/spendwise-backend
    ```
    *(Repeat for ai-service and frontend)*
2. In AWS RDS, create a PostgreSQL 15 database instance.
3. In AWS DocumentDB or MongoDB Atlas, create your NoSQL cluster.
4. Create an ECS Fargate Task Definition referencing the ECR images and RDS/Mongo endpoints as Environment Variables.
5. Launch the ECS Service and expose the Frontend through an Application Load Balancer (ALB).

### Option C: AWS AppRunner (PaaS)
If you don't want to manage load balancers, deploy your frontend and backend separately using AWS AppRunner connected directly to your GitHub repository or ECR.

---
**Congratulations! SpendWise AI is fully synthesized, architected, and containerized!**
