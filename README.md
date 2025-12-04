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
'''mermaid
flowchart TD
    A[Client / Frontend] --> B[Application Load Balancer]
    B --> C[EC2 Backend API (Gunicorn)]
    C --> D[LLM Server]
'''

## Features
- Fully automated CI/CD pipeline
- Zero-downtime deployment
- ALB + health checks
- systemd-managed backend API
- Environment variables support
- Secure SSH key deployment

## Project Structure
'''
backend-api/
│── app.py
│── requirements.txt
│── .env
│── venv/
│── systemd/backend-api.service
└── .github/workflows/ci-cd.yml
'''
