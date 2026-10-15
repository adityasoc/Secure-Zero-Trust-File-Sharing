# Security Documentation

## 1. Project Overview

Project Name: Secure Zero-Trust File Sharing Platform with Threat Detection

This project implements a secure file-sharing application using authentication, encrypted file storage, and ownership-based access control.

## 2. Zero-Trust Security Approach

The application follows the principle of never automatically trusting a user or request.

- Users must authenticate before accessing protected resources.
- File access is restricted according to ownership.
- Unauthorized file access requests are rejected.
- Authentication tokens are used to identify authenticated users.
- Encrypted file contents are protected against unauthorized modification.

## 3. Authentication and Password Protection

The application provides user registration and login functionality.

- Passwords are hashed using Argon2.
- JWT tokens are used for authenticated API requests.
- Protected endpoints require appropriate authentication.
- JWT signing secrets must remain private and should be rotated if exposed.

## 4. File Encryption

The application uses AES-256-GCM authenticated encryption.

- A 256-bit encryption key is configured through the backend environment.
- A 12-byte nonce is used for encryption operations.
- Authenticated encryption helps detect unauthorized changes to encrypted content.
- The encryption key must be stored securely and must not be committed to a public repository.

## 5. File Access Control

The backend applies ownership-based access control to file downloads.

- Authenticated users can access files they are authorized to access.
- Attempts to download another user's file are rejected.
- Unsupported file extensions are restricted.
- The configured maximum upload size is 10 MB.

## 6. Security Logging

The application maintains security-related logs to support troubleshooting and investigation.

The configured logging system writes events to:

`backend/logs/security.log`

Log files use rotation to limit their size and retain a limited number of backups.

Logs should not contain passwords, JWT tokens, encryption keys, or other sensitive credentials.

## 7. Database Security

PostgreSQL stores the application's structured data.

Recommended protections include:

- Use a dedicated database account with limited privileges.
- Keep database credentials in environment variables.
- Restrict database network access.
- Back up the database securely.
- Avoid exposing database credentials in screenshots or documentation.

## 8. Configuration and Secret Management

The backend uses a `.env` file for sensitive configuration.

The following files and information must not be published:

- `.env` files containing secrets
- JWT signing secrets
- Encryption keys
- Database passwords
- User credentials and access tokens
- Private logs containing sensitive information

A public deployment should use appropriately managed secrets and production-grade configuration.

## 9. Current Scope and Limitations

This documentation describes the security controls implemented in the current local project.

Automated threat detection, advanced alerting, malware scanning, and production deployment security should not be considered implemented unless they are separately developed and tested.

## 10. Security Recommendations

- Rotate any secret that may have been exposed.
- Use HTTPS in deployed environments.
- Apply rate limiting to authentication endpoints.
- Validate uploaded files beyond their extensions.
- Keep dependencies updated.
- Run automated security tests before releases.
- Review logs regularly.
- Conduct an independent security assessment before production use.

## 11. Disclaimer

This project is intended for educational and demonstration purposes. Production deployment requires additional hardening, testing, monitoring, and security review.
