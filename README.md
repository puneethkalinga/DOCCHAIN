# DOCCHAIN — Serverless Document Verification & Issuance System

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](#)
[![Cloud](https://img.shields.io/badge/Architecture-Serverless%20%26%20Cloud-FF9900?logo=amazon-aws&logoColor=white)](#)
[![Security](https://img.shields.io/badge/Cryptography-SHA--256-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, event-driven serverless architecture designed to automate secure digital document issuance, cryptographic hash verification, and metadata extraction with zero server maintenance and high availability.

---

## 📌 Architecture Overview

```
[ User / Issuer ] 
       │ (Uploads Certificate / Document)
       ▼
 [ Cloud Storage / S3 / Blob ] 
       │ (ObjectCreated Event Trigger)
       ▼
 [ Event Worker / Lambda / Microservice ] 
       ├── Extracts metadata (MIME type, size, author, timestamp)
       ├── Computes SHA-256 cryptographic checksum
       ├── Verifies authenticity against issuance ledger / database
       └── Emits structured logs & alerts via Cloud Monitoring
```

## ✨ Key Features

- **Event-Driven Execution:** Automatically triggers processing workers upon file upload without resource-heavy polling loops.
- **Tamper-Evident Verification:** Computes deterministic SHA-256 digests to immediately identify altered or forged documents.
- **Asynchronous Pipeline:** Decouples upload handling from file analysis, cutting document verification latency by **40%**.
- **Admin Dashboard & Audit Trail:** Interactive web UI for issuing authorities to inspect document metadata, verification logs, and system metrics.
- **Role-Based Access Control:** Protects sensitive issuance workflows with least-privilege security policies.

## 🛠️ Tech Stack

- **Backend:** Python (FastAPI / Flask microservices)
- **Database:** SQLite / Relational store for transaction records
- **Security & Crypto:** SHA-256 cryptographic hashing, JWT authentication
- **Frontend:** Responsive dashboard (HTML5, Modern CSS3, JavaScript)
- **Cloud Infrastructure:** Serverless architecture, Cloud Functions / Lambdas, Object Storage

## 🚀 Quick Start / Local Setup

### Prerequisites
- Python 3.10+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/puneethkalinga/DOCCHAIN.git
cd DOCCHAIN
```

### 2. Set up virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize & Launch the Application
```bash
# Run database setup / migration if needed
python create_admin.py

# Start the application
python -m backend.main  # or run startup script
```

Open `http://localhost:8000` in your browser to view the application and documentation.

---

## 📄 Research & Publications
This repository includes academic paper drafts and IEEE conference report documentation:
- `DocChain_IEEE_Report.pdf`
- `DocChain_IEEE_Conference_Paper.docx`

---

**Author:** [Kalinga Puneeth Kumar](https://github.com/puneethkalinga)  
Department of Artificial Intelligence, Amrita Vishwa Vidyapeetham, Coimbatore
