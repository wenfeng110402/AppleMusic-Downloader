# Contributing Guide

Thank you for your interest in contributing to AppleMusic Downloader (`amdl`). This guide outlines the development workflow, coding standards, and procedures for submitting contributions.

---

## Development Prerequisites

The project comprises a Python backend (FastAPI / gamdl), a Next.js TypeScript frontend, and an optional pywebview desktop runtime.

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (with `npm`)
- **External Binaries**: `ffmpeg` (for media processing) and `N_m3u8DL-RE` (optional stream engine)

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
```

### 2. Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install core development dependencies
pip install -e .

# For desktop GUI support:
pip install -e ".[desktop]"
```

### 3. Frontend Setup

```bash
cd src/frontend
npm install
```

---

## Running in Development

### Full-Stack Mode (Recommended)

1. **Start the API server (Terminal 1)**:
   ```bash
   python3 -m amdl server --host 127.0.0.1 --port 8000
   ```

2. **Start the Next.js dev server with hot reload (Terminal 2)**:
   ```bash
   cd src/frontend
   npm run dev
   ```
   Access `http://localhost:3000` to interact with the frontend. API calls are automatically proxied to port 8000.

### Desktop Mode

```bash
python3 -m amdl desktop
```

---

## Building Frontend Assets

Production desktop builds and server distributions serve static files from `src/frontend/out/`. If you modify any frontend code, compile the static distribution:

```bash
cd src/frontend
npm run build
```

Verify that the build completes without TypeScript or linting errors.

---

## Coding Standards

- **Formatting**: Adhere to [`.editorconfig`](.editorconfig). Use 4 spaces for Python files, 2 spaces for TypeScript/CSS/JSON, and enforce `LF` line endings across all files.
- **Python**: Follow PEP 8 guidelines and maintain comprehensive type annotations.
- **Frontend**: Write clean, modular TypeScript components using existing Tailwind design tokens and CSS variables. Avoid unnecessary external dependencies.
- **Internationalization**: Ensure any new user-facing strings are added to both `zh` and `en` dictionaries in `src/frontend/app/i18n.tsx`.

---

## Submitting Pull Requests

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes using descriptive, conventional commit messages:
   ```text
   feat: add syllable lyrics parsing
   fix: resolve CLI routing issue with option flags
   ```
3. Test both backend imports and frontend build before pushing:
   ```bash
   python3 -c "import amdl.cli, amdl.core_downloader, amdl.server"
   cd src/frontend && npm run build
   ```
4. Push to your fork and submit a Pull Request to `main`.
