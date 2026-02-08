# Test Applications Manager

### App on AWS: <https://karnetic-labs.com/>

![TAM screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/tam.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Django Apps](#django-apps)
  - [Core](#core)
  - [Accounts](#accounts)
  - [Taberna (E-Commerce)](#taberna-e-commerce)
  - [Social Network](#social-network)
  - [AI Lab](#ai-lab)
  - [Donation](#donation)
- [API Endpoints](#api-endpoints)
- [Scheduled Tasks (Celery Beat)](#scheduled-tasks-celery-beat)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Local Development](#local-development)
  - [Front-end Development](#front-end-development)
- [Makefile Commands](#makefile-commands)
- [Docker](#docker)
  - [Development](#development)
  - [Production](#production)
- [Testing & Linting](#testing--linting)
- [CI/CD](#cicd)
- [Deployment](#deployment)

---

## Overview

**Test Applications Manager (TAM)** is a multi-purpose Django web platform that combines several independent modules into a single deployment:

- **Portfolio** -- project showcase with categories, tags, and image galleries.
- **Taberna** -- a full-featured e-commerce store with products, variations, cart, orders, reviews, and Stripe/PayPal payments.
- **Social Network** -- profiles, friend system, posts with hashtags/trends, real-time chat and notifications via WebSockets.
- **AI Lab** -- chat, image generation, voice generation, and vision powered by the OpenAI API.
- **Donation** -- PayPal-based donation flow.

The application is containerized with Docker, uses PostgreSQL as the database, Redis for caching/channels/Celery broker, and is deployed on AWS behind an Nginx reverse proxy with Let's Encrypt SSL.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.1, Django REST Framework 3.16.1 |
| Authentication | JWT (SimpleJWT 5.5.1), Djoser 2.3.3 |
| Database | PostgreSQL 17 |
| Cache / Broker | Redis 7.4.2 |
| Task Queue | Celery 5.6.2, Celery Beat |
| WebSockets | Django Channels 4.3.2, Channels-Redis |
| Payments | Stripe 14.3.0, django-paypal 2.1 |
| AI | OpenAI 2.16.0 |
| Rich Text | django-ckeditor-5 |
| Frontend Build | Webpack, SCSS, Bootstrap 5, jQuery |
| ASGI Server | Uvicorn 0.40.0 |
| WSGI Server | Gunicorn 25.0.0 |
| Reverse Proxy | Nginx 1.27.4 |
| SSL | Let's Encrypt (Certbot 4.0.0) |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Linting | Flake8 7.3.0, djLint 1.36.4 |
| Testing | Django TestCase, Coverage 7.13.2 |

---

## Project Structure

```
karnetic-labs/
├── .github/workflows/        # CI/CD pipeline (GitHub Actions)
│   └── checks.yml
├── docker/
│   ├── certbot/               # SSL certificate management
│   └── proxy/                 # Nginx reverse proxy configuration
├── portfolio/                 # Django project root
│   ├── apps/                  # All Django applications
│   │   ├── accounts/          # Custom user authentication
│   │   ├── ai_lab/            # AI-powered features (OpenAI)
│   │   ├── core/              # Portfolio showcase
│   │   ├── donation/          # PayPal donations
│   │   ├── social_chat/       # Real-time WebSocket chat
│   │   ├── social_notification/ # Real-time notifications
│   │   ├── social_posts/      # Social feed, likes, comments, trends
│   │   ├── social_profiles/   # Social profiles & friend system
│   │   ├── taberna_cart/      # Shopping cart
│   │   ├── taberna_orders/    # Order & payment processing
│   │   ├── taberna_product/   # Product catalog & reviews
│   │   └── taberna_profiles/  # E-commerce user profiles
│   ├── templates/             # Django HTML templates
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL configuration
│   ├── asgi.py                # ASGI config (WebSocket support)
│   ├── wsgi.py                # WSGI config
│   └── celery.py              # Celery configuration
├── scripts/
│   └── run.sh                 # Production startup script
├── static/                    # Collected static files
├── docker-compose.yml         # Development services
├── docker-compose.deploy.yml  # Production services
├── Dockerfile                 # Application image (Python 3.12-alpine)
├── Makefile                   # Build, test, deploy shortcuts
├── manage.py                  # Django management entry point
├── requirements.txt           # Python dependencies
├── setup.cfg                  # Flake8 configuration
├── .coveragerc                # Coverage settings
└── .env.sample                # Environment variables template
```

---

## Django Apps

### Core

The **portfolio showcase** module. Displays projects with categories, tags, and image galleries.

| Model | Purpose |
|---|---|
| `Category` | Project categories |
| `Tag` | Project tags |
| `Project` | Portfolio project entry |
| `ProjectGallery` | Image gallery for projects |

Frontend is built with Webpack (source in `portfolio/apps/core/_dev/`).

### Accounts

Custom user authentication built on `AbstractBaseUser`.

| Model | Purpose |
|---|---|
| `Account` | Custom user model with email-based login |

Provides REST API serializers and endpoints for registration, login, and profile management.

### Taberna (E-Commerce)

A complete online store split into four apps:

#### taberna_product -- Product Catalog

| Model | Purpose |
|---|---|
| `Category` | Product categories |
| `Product` | Product with Stripe product ID |
| `Variation` | Size/color variants (custom `VariationManager`) |
| `ReviewRating` | Customer reviews and ratings |
| `ProductGallery` | Product images |

Frontend is built with Webpack (source in `portfolio/apps/taberna_product/_dev/`).

#### taberna_cart -- Shopping Cart

| Model | Purpose |
|---|---|
| `Cart` | Shopping cart (session-based) |
| `CartItem` | Individual cart line items with variation support |

Includes a context processor for cart item count across all templates.

#### taberna_orders -- Orders & Payments

| Model | Purpose |
|---|---|
| `Payment` | Payment record (Stripe integration) |
| `Order` | Customer order with status tracking |
| `OrderProduct` | Individual ordered items |

Order statuses: **New** -> **Accepted** -> **Completed** / **Cancelled**. Sends email notifications on order placement.

#### taberna_profiles -- User Profiles

| Model | Purpose |
|---|---|
| `UserProfile` | OneToOne profile with address and avatar |

### Social Network

Real-time social platform with four apps:

#### social_profiles -- Profiles & Friends

| Model | Purpose |
|---|---|
| `Profile` | Social profile (OneToOne with Account) |
| `FriendshipRequest` | Friend request management |

Supports friend suggestions, friend requests (accept/reject), and profile browsing.

#### social_posts -- Feed & Trends

| Model | Purpose |
|---|---|
| `Post` | User posts (UUID primary key) |
| `Like` | Post likes |
| `Comment` | Post comments (UUID primary key) |
| `PostAttachment` | Media attachments |
| `Trend` | Auto-generated hashtag trends |

#### social_chat -- Real-Time Chat

| Model | Purpose |
|---|---|
| `Conversation` | Chat conversation (UUID primary key) |
| `ConversationMessage` | Individual messages |

WebSocket consumer: `SocialChatConsumer` (Django Channels).

#### social_notification -- Notifications

| Model | Purpose |
|---|---|
| `Notification` | Notification (friend requests, likes, comments, messages) |

WebSocket consumer: `NotificationConsumer` for real-time push.

### AI Lab

AI-powered features using the OpenAI API:

- **Chat** -- conversational AI endpoint
- **Image Generation** -- AI image creation
- **Voice Generation** -- text-to-speech
- **Vision** -- image upload and analysis
- **Realtime Tokens** -- token generation for streaming

Generated media is automatically cleaned up daily.

### Donation

PayPal Standard IPN integration for accepting donations.

| Model | Purpose |
|---|---|
| `Donation` | Donation record |
| `Transaction` | Payment transaction log |

---

## API Endpoints

| Prefix | App | Protocol |
|---|---|---|
| `/` | Core (portfolio) | HTTP |
| `/admin/` | Django Admin | HTTP |
| `/api/v1/auth/` | Djoser authentication | HTTP |
| `/api/v1/token/` | JWT token (obtain/refresh) | HTTP |
| `/taberna-store/` | Product catalog | HTTP |
| `/taberna-cart/` | Shopping cart | HTTP |
| `/taberna-orders/` | Orders | HTTP |
| `/taberna-profiles/` | E-commerce profiles | HTTP |
| `/api/social-posts/` | Social feed | HTTP |
| `/api/social-profiles/` | Social profiles | HTTP |
| `/api/social-chat/` | Chat API | HTTP |
| `/api/social-notifications/` | Notifications API | HTTP |
| `/ai-lab/` | AI Lab | HTTP |
| `/donation/` | Donations | HTTP |
| `/paypal/` | PayPal IPN | HTTP |
| `/ckeditor5/` | Rich text editor | HTTP |
| `/ws/` | WebSocket (chat, notifications) | WS |

---

## Scheduled Tasks (Celery Beat)

| Time (UTC) | Task | Description |
|---|---|---|
| 02:00 | `delete_generated_media` | Clean up AI-generated media files |
| 03:00 | `delete_old_carts` | Remove abandoned shopping carts |
| 04:00 | `create_social_posts_trends` | Aggregate hashtag trends from posts |
| 04:30 | `delete_old_rejected_friendship_requests` | Purge expired friend requests |
| 05:00 | `create_social_friend_suggestions` | Generate friend suggestions |

---

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose**
- **Node.js 22.x** (for frontend development, via `nvm`)
- **Git**

### Environment Variables

Copy the sample file and fill in your values:

```bash
cp .env.sample .env
```

| Variable | Description |
|---|---|
| `SQL_ENGINE` | Database backend (`django.db.backends.postgresql`) |
| `SQL_DATABASE` | PostgreSQL database name |
| `SQL_USER` | PostgreSQL user |
| `SQL_PASSWORD` | PostgreSQL password |
| `SQL_HOST` | Database host (`db` for Docker) |
| `SECRET_KEY` | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | Allowed host(s) |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins |
| `EMAIL_HOST` | SMTP server |
| `EMAIL_PORT` | SMTP port (default `587`) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `EMAIL_USE_TLS` | Enable TLS (`1` / `0`) |
| `PAYPAL_RECEIVER_EMAIL` | PayPal business email |
| `PAYPAL_TEST` | PayPal sandbox mode (`True` / `False`) |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key |
| `STRIPE_PRIVATE_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `OPENAI_API_KEY` | OpenAI API key |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key |
| `APP_LOCAL_SERVER` | Dev server: `runserver` or `uvicorn` |

### Local Development

```bash
# 1. Clone the repository
git clone <repo-url> && cd karnetic-labs

# 2. Copy and configure environment variables
cp .env.sample .env

# 3. Build and start all services
make build

# 4. Create a superuser
make super

# 5. Open in browser
# http://localhost:8000
```

The development stack spins up: Django app, PostgreSQL, Redis, Celery worker, Celery Beat, and Flower (monitoring at `http://localhost:5555`).

To switch between Django's built-in `runserver` and `uvicorn` (for WebSocket support), set the `APP_LOCAL_SERVER` variable in `.env`.

### Front-end Development

Both frontend modules require **Node.js 22.x**.

#### Taberna Store

```bash
nvm use 22.19.0
cd portfolio/apps/taberna_product/_dev
npm install
npm run w
```

#### Core (Portfolio)

```bash
nvm use 22.19.0
cd portfolio/apps/core/_dev
npm install
npm run w
```

---

## Makefile Commands

### Development

| Command | Description |
|---|---|
| `make run` | Start containers (no rebuild) |
| `make build` | Build images, start containers, prune old images |
| `make test` | Run Flake8 + Coverage tests, generate HTML report |
| `make stop` | Backup database and stop containers |
| `make backup` | Restore database from `temp/db_backup.sql` |
| `make migrate` | Generate and apply Django migrations |
| `make super` | Create a Django superuser |
| `make clean` | Prune Docker images, volumes, and build cache |
| `make update` | Update all Python + JS dependencies, rebuild, test |

### Frontend

| Command | Description |
|---|---|
| `make update_front_taberna` | Update and rebuild Taberna frontend |
| `make update_front_core` | Update and rebuild Core frontend |

### Production (Remote Host)

| Command | Description |
|---|---|
| `make prod` | Pull main branch, build, migrate, deploy |
| `make dev` | Pull development branch, build, migrate, deploy |
| `make proxy` | Reset SSL certificates and restart Nginx proxy |
| `make db-backup-restore` | Restore production database from backup |

---

## Docker

### Development

**`docker-compose.yml`** defines the following services:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `app` | Custom (Python 3.12-alpine) | 8000 | Django application |
| `db` | postgres:17-alpine | -- | PostgreSQL database |
| `redis` | redis:7.4.2-alpine | 6379 | Cache, Channels layer, Celery broker |
| `celery` | Custom | -- | Celery worker |
| `celery-beat` | Custom | -- | Celery periodic task scheduler |
| `flower` | mher/flower | 5555 | Celery task monitoring dashboard |

Source code is volume-mounted for hot reload.

### Production

**`docker-compose.deploy.yml`** adds:

| Service | Image | Port | Purpose |
|---|---|---|---|
| `proxy` | Custom (nginx:1.27.4-alpine) | 80, 443 | Nginx reverse proxy with SSL |
| `certbot` | Custom (certbot 4.0.0) | -- | Let's Encrypt SSL certificates |

Production features:
- Gunicorn + Uvicorn workers
- HTTP to HTTPS redirect
- WebSocket proxying (`/ws/`, `/wss/`)
- Static file serving from Docker volume
- SSL/TLS with automatic certificate renewal
- PostgreSQL performance tuning
- Celery memory limits

---

## Testing & Linting

```bash
# Run full test suite with linting and coverage
make test
```

This executes:
1. **Flake8** -- Python code style checks (configured in `setup.cfg`, max line length 140)
2. **Coverage** -- runs Django tests and generates an HTML coverage report
   - Excludes: migrations, admin, urls, apps configs (see `.coveragerc`)

---

## CI/CD

GitHub Actions workflow (`.github/workflows/checks.yml`) runs on every push:

1. **Login** to Docker Hub
2. **Checkout** the source code
3. **Test** -- waits for database, runs Django test suite
4. **Lint** -- runs Flake8

Secrets required in GitHub repository settings:
- `DOCKERHUB_USER`, `DOCKERHUB_TOKEN`
- `SQL_ENGINE`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`, `SQL_HOST`
- `DJANGO_SECRET_KEY`
- `STRIPE_PRIVATE_KEY`

---

## Deployment

The application is deployed on **AWS** with Docker Compose:

1. SSH into the remote host
2. Run `make prod` (or `make dev` for the development branch)
3. The Makefile pulls the latest code, rebuilds containers, runs migrations, and starts services
4. Nginx serves the application over HTTPS with Let's Encrypt SSL
5. For initial SSL setup, run `make proxy` to obtain certificates

Production URL: **<https://karnetic-labs.com/>**
