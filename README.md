# Videoflix Backend

Backend for Videoflix, a small video streaming platform built with Django REST Framework.
Users register, activate their account by email and watch videos in different resolutions.
Uploaded videos are converted to HLS in the background.

## Tech stack

Django, Django REST Framework, PostgreSQL, Redis, Django-RQ, FFmpeg, Docker

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

## Setup

Clone the repository:

```bash
git clone https://github.com/Mickida/videoflix_Backend.git
```

```bash
cd videoflix_Backend
```

Create the `.env` file from the template.

Git Bash, macOS or Linux:

```bash
cp .env.template .env
```

Windows PowerShell:

```powershell
Copy-Item .env.template .env
```

Fill in the values in `.env` (database, superuser and email account).
To print emails to the Docker log instead of sending them, set
`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`.

Build and start the containers:

```bash
docker compose up --build
```

The backend runs on `http://127.0.0.1:8000`.

## Usage

Log in to the admin at `http://127.0.0.1:8000/admin/` with the superuser from `.env`
and upload a video. It can be streamed once its status is **Ready**.

Open the frontend at `http://127.0.0.1:5500` (not `localhost`), so that the login cookies work.
