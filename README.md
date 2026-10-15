# Secure Zero-Trust File Sharing Platform

A secure file-sharing web application built with FastAPI, PostgreSQL, and JavaScript.

## Features

- User registration and login
- JWT-based authentication
- Argon2 password hashing
- AES-256-GCM file encryption
- Ownership-based file access control
- Secure file upload and download
- PostgreSQL database integration
- Security event logging
- Responsive web interface

## Technology Stack

- Backend: Python and FastAPI
- Frontend: HTML, CSS, JavaScript
- Database: PostgreSQL
- Authentication: JWT
- Password hashing: Argon2
- File encryption: AES-256-GCM

## Installation

### 1. Clone the repository

    git clone https://github.com/adityasoc/Secure-Zero-Trust-File-Sharing.git
    cd Secure-Zero-Trust-File-Sharing

### 2. Install dependencies

    python -m pip install -r requirements.txt

### 3. Start the backend

    cd backend
    python -m uvicorn main:app --reload

API documentation: http://127.0.0.1:8000/docs

### 4. Start the frontend

Open another PowerShell terminal in the project root and run:

    python -m http.server 5500 --directory frontend

Frontend: http://127.0.0.1:5500

## Security

- Password hashing using Argon2
- JWT-based authentication
- AES-256-GCM encryption
- Ownership-based file access restrictions
- Security event logging

Configure PostgreSQL and the required environment variables before starting the application. Never upload your actual .env file or secret keys to GitHub.

## Future Enhancements

- Automated threat detection and alerting
- Malware scanning
- API rate limiting
- Additional automated security tests

## Disclaimer

This project is intended for educational and demonstration purposes. Production deployment requires further security testing and hardening.
