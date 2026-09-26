# Security Policy

## Supported Versions

Only the latest release of AppleMusic Downloader receives active security updates and patches.

| Version | Supported          |
| ------- | ------------------ |
| 2.5.x   | :white_check_mark: |
| < 2.5   | :x:                |

## Credentials and Privacy

AppleMusic Downloader is designed with strict respect for user privacy and credential security:

1. **No Data Collection**: This software does not upload, log, track, or share your `cookies.txt`, Apple ID credentials, tokens, or download activity with any external servers.
2. **Direct Communication**: All network requests occur directly between your local machine and official Apple endpoints (`*.apple.com`) over secure HTTPS.
3. **Local Storage**: Your credentials remain on your local disk. Please ensure your `cookies.txt` file is stored securely and excluded from public version control (e.g. by adding it to `.gitignore`).

## Reporting a Vulnerability

If you discover a security vulnerability in this project:

- Please do **not** open a public issue.
- Report it privately via GitHub [Private Vulnerability Reporting](https://github.com/wenfeng110402/AppleMusic-Downloader/security/advisories/new).
- Provide detailed steps to reproduce the issue, including relevant logs or proof of concept.

We will review reports promptly and publish patches in subsequent minor releases.
