# System Architecture

## 1. Overview

The Secure Zero-Trust File Sharing Platform is a web application designed to protect files through encryption, authentication, authorization, and security event logging.

## 2. Architecture Components

### Frontend
The frontend is developed using HTML, CSS, and JavaScript. It provides the dashboard and allows users to register, log in, upload files, and download authorized files.

### Backend API
The backend uses Python and FastAPI. It handles incoming requests, validates user authentication, applies file access rules, and coordinates database and file operations.

### Database
PostgreSQL stores application records and related metadata. SQLAlchemy is used for database interaction.

### Encryption
AES-256-GCM is used to protect file contents and verify encrypted data integrity during decryption.

### Security Logging
The security logger records relevant events, including authentication activity, file operations, and denied access attempts.

## 3. Request Flow

1. The user interacts with the frontend.
2. The frontend sends an HTTP request to the backend API.
3. The backend authenticates the user when required.
4. The backend validates the requested operation and file ownership.
5. The database and encryption components process the operation.
6. The backend returns the result to the frontend.
7. Relevant security events are logged.

## 4. Local Development Ports

- Frontend: `http://127.0.0.1:5500`
- Backend API: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/docs`

## 5. Security Boundaries

The frontend is not a trusted security boundary. Authentication, authorization, and file access decisions must be enforced by the backend.

Secrets and encryption keys must be stored outside source control. Production deployment should use HTTPS, secure secret management, restricted network access, and additional security testing.
