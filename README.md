# 🌎 Wildfire Monitoring System 🔥

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange)](https://aws.amazon.com/lambda/)
[![Ansible](https://img.shields.io/badge/Ansible-Automation-red)](https://www.ansible.com/)
[![S3](https://img.shields.io/badge/AWS-S3-blue)](https://aws.amazon.com/s3/)
[![API Gateway](https://img.shields.io/badge/API-Gateway-yellow)](https://aws.amazon.com/api-gateway/)
[![DynamoDB](https://img.shields.io/badge/DynamoDB-NoSQL-green)](https://aws.amazon.com/dynamodb/)
[![SNS](https://img.shields.io/badge/SNS-Notifications-purple)](https://aws.amazon.com/sns/)
[![EventBridge](https://img.shields.io/badge/EventBridge-Scheduling-blueviolet)](https://aws.amazon.com/eventbridge/)

🚀 **Automated wildfire detection and alerting system using AWS Lambda, S3, DynamoDB, SNS, API Gateway, and EventBridge.**

---

## 📌 Overview
The **Wildfire Monitoring System** is a cloud-based solution that detects wildfires in real-time using **NASA's VIIRS and MODIS satellite data**. The system provides **automated alerts** to **subscribed users** based on **geographical wildfire activity**.

### ✅ **Key Features:**
- **Frontend Webpage:** Simple **webpage hosted on S3** using **HTML, CSS, and JavaScript** for **user subscriptions**.
- **UserOnboardingFunction:** Handles **user sign-ups**, **stores user data in DynamoDB**, and **subscribes users to location-specific SNS topics**.
- **DailyMonitoringFunction:** **Scheduled via EventBridge** to **fetch wildfire data**, **filter by FRP and user location**, and **send targeted alerts**.
- **Ansible Automation:** Automates the **packaging and deployment** of **Lambda functions**.

---

## 🛠️ **Architecture**

### **System Components:**
1. **Frontend:** S3-hosted webpage for **user input**.
2. **API Gateway:** Receives **subscription requests**.
3. **Lambda Functions:**
   - **UserOnboardingFunction:** Processes **user subscriptions**.
   - **DailyMonitoringFunction:** **Fetches wildfire data** and **sends alerts**.
4. **DynamoDB:** Stores **user email and zip code**.
5. **SNS:** Sends **email alerts** to **subscribed users**.
6. **EventBridge:** Triggers **daily wildfire data processing**.
7. **S3 Bucket:** Stores **filtered wildfire data**.

### 📈 **Architecture Diagram:**

<img src="architecture_diagram.svg" alt="Wildfire Monitoring Architecture" width="800">

---

## 🚀 **Deployment Instructions**

### **1️⃣ Prerequisites:**
- **AWS Account**
- **Ansible Installed:**
```sh
brew install ansible
