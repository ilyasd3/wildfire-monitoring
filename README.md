# 🌎 Wildfire Monitoring System 🔥

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![S3](https://img.shields.io/badge/AWS-S3-blue?logo=amazons3&logoColor=white)](https://aws.amazon.com/s3/)
[![API Gateway](https://img.shields.io/badge/API-Gateway-red?logo=amazonapigateway&logoColor=white)](https://aws.amazon.com/api-gateway/)
[![DynamoDB](https://img.shields.io/badge/DynamoDB-NoSQL-4053D6?logo=amazon-dynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![SNS](https://img.shields.io/badge/SNS-Notifications-orange?logo=amazonsns&logoColor=white)](https://aws.amazon.com/sns/)
[![EventBridge](https://img.shields.io/badge/EventBridge-Scheduling-FF4F8B?logo=amazoneventbridge&logoColor=white)](https://aws.amazon.com/eventbridge/)
[![Ansible](https://img.shields.io/badge/Ansible-Automation-ee0000?logo=ansible&logoColor=white)](https://www.ansible.com/)

**Automated wildfire detection and alerting system using AWS Lambda, S3, DynamoDB, SNS, API Gateway, and EventBridge.**

---

## 📌 Overview
The **Wildfire Monitoring System** is a cloud-based solution that detects wildfires in real-time using **NASA's MODIS satellite data**. The system provides **automated alerts** to **subscribed users** based on **geographical wildfire activity**.

### ✅ **Key Features:**
- **Frontend Webpage:** Simple **webpage hosted on S3** using **HTML, CSS, and JavaScript** for **user subscriptions**.
- **UserOnboardingFunction:** Handles **user sign-ups**, **stores user data in DynamoDB**, and **subscribes users to location-specific SNS topics**.
- **DailyMonitoringFunction:** **Scheduled via EventBridge** to **fetch wildfire data**, **filter by FRP and user location**, and **send targeted alerts**.
- **Ansible Automation:** Automates the **packaging and deployment** of **Lambda functions**.

---

## 🛠️ **Architecture Diagram**

<img src="architecture_diagram.svg" alt="Wildfire Monitoring Architecture" width="800">

---

## 🚀 **Deployment Instructions**

### **1️⃣ Prerequisites:**
- **AWS Account**
- **Ansible Installed:**
```sh
brew install ansible
```

### **2️⃣ Clone the Repository:**
```sh
git clone https://github.com/ilyasd3/wildfire-monitoring.git
cd wildfire-monitoring
```

### **3️⃣ Deploy Lambda Functions with Ansible:**
```sh
cd ansible
ansible-playbook lambda_deployment.yml
```

---

## 🔥 **How It Works**

### 🟢 **User Initiated Flow:**
1. **User enters email and zip code** on **S3-hosted website**.
2. **POST request** is sent to **API Gateway**.
3. **API Gateway triggers UserOnboardingFunction**.
4. **Lambda function subscribes user to SNS topic** based on **zip code**.
5. **Stores user data in DynamoDB**.

### 🟢 **Scheduled Alerts Flow:**
1. **EventBridge triggers DailyMonitoringFunction** on a **recurring schedule**.
2. **Lambda function fetches user data** from **DynamoDB**.
3. **Fetches wildfire data** from the **NASA FIRMS API**.
4. **Processes data** based on **user zip codes** and **FRP**.
5. **Stores filtered data in S3 bucket**.
6. **Sends email alerts** to **subscribed users** via **SNS**.

---

## 🤝 **Contributing**
Feel free to **open issues**, **submit PRs**, or **suggest features**!
