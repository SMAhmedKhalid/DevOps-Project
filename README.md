# Backend API — Flask + Gunicorn + EC2 + ALB + GitHub Actions CI/CD

## Overview
This project is a production-ready Flask backend hosted on AWS using:
- EC2 Instance (Ubuntu Server)
- Gunicorn + systemd
- Application Load Balancer (ALB)
- Auto Scaling Group
- GitHub Actions CI/CD pipeline (Automated)
- SSH-based deployment on push to '''main'''

## Architecture
```mermaid
flowchart TD
    A[Client / Frontend] --> B[Application Load Balancer]
    B --> C[EC2 Backend API (Gunicorn)]
    C --> D[LLM Server]
```

## Features
- Fully automated CI/CD pipeline
- Zero-downtime deployment
- ALB + health checks
- systemd-managed backend API
- Environment variables support
- Secure SSH key deployment

## Project Structure
```
backend-api/
│── app.py
│── requirements.txt
│── .env
│── venv/
│── systemd/backend-api.service
└── .github/workflows/ci-cd.yml
```

## Local Setup
### 1. Clone the repo
```bash
git clone https://github.com/your/repo.git
cd backend-api
```

### 2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. AWS Deployment Setup
**EC2 Setup**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git
```

**systemd Service File**
```bash
sudo nano /etc/systemd/system/backend-api.service
```

**In the file, paste:**
```bash
[Unit]
Description=Backend API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/backend-api
Environment=PATH=/home/ubuntu/backend-api/venv/bin
ExecStart=/home/ubuntu/backend-api/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## GitHub Actions CI/CD
### Workflow File
```yaml
# File: .github/workflows/deploy.yml

name: Deploy Backend API

on:
  push:
    branches: [ "main" ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts || true

      - name: Deploy to EC2
        run: |
          ssh -o StrictHostKeyChecking=no ubuntu@${{ secrets.EC2_HOST }} << 'EOF'
          cd /home/ubuntu/backend-api
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl daemon-reload
          sudo systemctl restart backend-api
          sudo systemctl status backend-api --no-pager
          EOF
```

## API Testing
### Health check
```bash
curl http://<ALB-DNS>/health
```

### Chat endpoint
```bash
curl -X POST http://<ALB-DNS>/api/chat \
     -H "Content-Type: application/json" \
     -d '{"session_id":"123","query":"Hello","email":"test@example.com"}'
```

## Troubleshooting
> Check logs
 ```bash
 sudo journalctl -u backend-api -f
```

> Check service status
```bash
sudo systemctl status backend-api
```


