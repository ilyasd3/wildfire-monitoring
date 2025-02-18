# 🌎 Wildfire Monitoring System 🔥

[![Terraform](https://img.shields.io/badge/Terraform-IaC-blueviolet)](https://www.terraform.io/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)](https://aws.amazon.com/lambda/)
[![Ansible](https://img.shields.io/badge/Ansible-Automation-red)](https://www.ansible.com/)

🚀 **Automated wildfire detection and alerting system using AWS Lambda, Terraform, and Ansible.**

## 📌 Overview

The **Wildfire Monitoring System** is a cloud-based solution designed to detect wildfires in real time using satellite data. It leverages **AWS Lambda**, **Terraform**, and **Ansible** to process data, automate deployment, and send alerts.

✅ **AWS Lambda** processes satellite wildfire data  
✅ **Terraform** provisions the infrastructure automatically  
✅ **Ansible** automates Lambda packaging and deployment  

🔥 **Goal:** Provide a scalable, automated wildfire monitoring system that can be deployed in any AWS account.

## 🛠️ Architecture

Below is the architecture of the Wildfire Monitoring System:

<img src="architecture_diagram.svg" alt="Wildfire Monitoring Architecture" width="800">

## 🚀 Deployment Instructions

Follow these steps to deploy the Wildfire Monitoring System:

### **1️⃣ Prerequisites**
- **AWS Account**
- **Terraform Installed** (`brew install terraform` or [Install Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli))
- **Ansible Installed** (`brew install ansible` or [Install Guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html))

### **2️⃣ Clone the Repository**
```sh
git clone https://github.com/ilyasd3/wildfire-monitoring.git
cd wildfire-monitoring
