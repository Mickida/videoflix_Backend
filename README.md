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
The `.env` file is not part of the repository, so the email settings must be your own
(see [Email](#email)).

Build and start the containers:

```bash
docker compose up --build
```

The backend runs on `http://127.0.0.1:8000`.

## Usage

Log in to the admin at `http://127.0.0.1:8000/admin/` with the superuser from `.env`
and upload a video. It can be streamed once its status is **Ready**.

Open the frontend at `http://127.0.0.1:5500` (not `localhost`), so that the login cookies work.

A new account can only log in after it was activated with the link from the activation email.

## Email

Example for Gmail (needs an [app password](https://myaccount.google.com/apppasswords),
the normal Gmail password does not work):

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your.address@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your.address@gmail.com
```

`DEFAULT_FROM_EMAIL` must be the same address as `EMAIL_HOST_USER`.
After changing `.env`, restart the containers:

```bash
docker compose up -d --force-recreate web
```
