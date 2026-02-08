# Donation

### App on AWS: <https://karnetic-labs.com/category/django/donation/>

![Donation screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/portfolio/apps/donation/donation.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Models](#models)
- [Views & URL Routes](#views--url-routes)
- [Payment Integrations](#payment-integrations)
  - [PayPal](#paypal)
  - [Stripe](#stripe)
- [Signals](#signals)
- [Templates](#templates)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Overview

**Donation** is a server-rendered Django module that provides a simple donation page with two payment options -- **PayPal** (Standard IPN) and **Stripe** (Checkout Sessions). A random donation amount is selected from the database and presented to the user. After payment, the app records the transaction and shows a success or failure page.

The module has no REST API -- it is fully template-based with server-side rendering.

---

## Architecture

```
Django Templates (Bootstrap + Stripe.js)
       │
       ├── PayPal Standard Form ──► PayPal ──► IPN callback (/paypal/)
       │                                             │
       │                                             ▼
       │                                      signals.py
       │                                      (validate & create Transaction)
       │
       └── Stripe Checkout Button ──► Stripe Checkout Session
                                             │
                                             ▼
                                      payment-success / payment-failed
```

---

## Models

### Donation

Represents a predefined donation option (title + amount).

| Field | Type | Details |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `title` | CharField(200) | Donation label |
| `amount` | DecimalField(4, 2) | Amount in USD (max 99.99) |

Donations are created via Django Admin. A random one is selected each time the donation page is loaded.

### Transaction

Records a completed payment.

| Field | Type | Details |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `invoice` | CharField(200) | Unique invoice identifier (UUID) |
| `title` | CharField(200) | Donation title from PayPal IPN |
| `amount` | DecimalField(4, 2) | Paid amount in USD |
| `paid` | BooleanField | default=False, set to True on successful payment |

---

## Views & URL Routes

Base: `/donation/`

| Pattern | View | Method | Template | Description |
|---|---|---|---|---|
| `/donation/` | `my_donation` | GET | `donation/includes/my-donation.html` | Main donation page with PayPal form and Stripe button |
| `/donation/payment-success/` | `payment_success` | GET | `donation/includes/payment-success.html` | Payment success confirmation |
| `/donation/payment-failed/` | `payment_failed` | GET | `donation/includes/payment-failed.html` | Payment failure / cancellation page |

### my_donation

1. Selects a random `Donation` from the database (falls back to a $10 default if none exist)
2. Builds a `PayPalPaymentsForm` with the donation details, a UUID invoice, and callback URLs
3. Creates a Stripe Checkout Session for the same donation
4. Renders the template with the PayPal form, Stripe session ID, and Stripe public key

### payment_success

Displays a confirmation page after a successful payment. Includes a 10-second delay to allow PayPal IPN processing to complete.

### payment_failed

Displays a cancellation / failure page when the user aborts or the payment fails.

---

## Payment Integrations

### PayPal

Uses `django-paypal` (PayPal Standard IPN).

**Flow:**
1. The donation page renders a `PayPalPaymentsForm` with:
   - `business` -- merchant email from `PAYPAL_RECEIVER_EMAIL`
   - `amount` -- donation amount
   - `item_name` -- donation title
   - `invoice` -- unique UUID4
   - `currency_code` -- USD
   - `notify_url` -- PayPal IPN endpoint (`/paypal/`)
   - `return_url` -- `/donation/payment-success/`
   - `cancel_return` -- `/donation/payment-failed/`
2. User completes payment on PayPal
3. PayPal sends an IPN callback to `/paypal/`
4. The `paypal_payment_received` signal handler validates and creates a `Transaction`

The PayPal IPN URL (`/paypal/`) is mounted in the root `urls.py` via `paypal.standard.ipn.urls`.

### Stripe

Uses the Stripe Checkout Sessions API.

**Flow:**
1. The donation page creates a Stripe Checkout Session with a predefined price ID
2. The template includes `Stripe.js v3` and a checkout button
3. Clicking the button redirects to Stripe's hosted checkout page
4. On completion, Stripe redirects to `/donation/payment-success/` or `/donation/payment-failed/`

---

## Signals

### paypal_payment_received

Listens to `valid_ipn_received` from `django-paypal`.

**Validation steps:**
1. Checks `payment_status == ST_PP_COMPLETED`
2. Validates `receiver_email` matches `PAYPAL_RECEIVER_EMAIL`
3. Asserts `mc_gross` matches the donation amount
4. Asserts `mc_currency` is `USD`

**On success:** Creates a `Transaction` record with `paid=True`.

**On failure:** Logs error messages (no transaction created).

---

## Templates

All templates are in `portfolio/templates/donation/`:

| Template | Purpose |
|---|---|
| `base.html` | Base layout with Bootstrap, Font Awesome, Stripe.js, and checkout button JS |
| `includes/my-donation.html` | Donation page -- renders PayPal form and Stripe checkout button |
| `includes/payment-success.html` | Payment success confirmation |
| `includes/payment-failed.html` | Payment failure / cancellation |

`base.html` includes the Stripe.js script and JavaScript that initializes `Stripe(stripe_public_key)` and binds the checkout button to `stripe.redirectToCheckout({ sessionId })`.

---

## Configuration

### Required Environment Variables

| Variable | Description |
|---|---|
| `PAYPAL_RECEIVER_EMAIL` | PayPal merchant / business email |
| `PAYPAL_TEST` | PayPal sandbox mode (`True` / `False`) |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key |
| `STRIPE_PRIVATE_KEY` | Stripe secret key |

### Admin Setup

Donation options are managed via Django Admin (`/admin/`). Create one or more `Donation` entries with a title and amount. If no donations exist, the view falls back to a default $10 donation.

---

## Testing

Tests are located in the `tests/` directory:

| Test File | Test Class | Coverage |
|---|---|---|
| `test_views.py` | `MyDonationViewTest` | Context variables, template, fallback when no donations exist |
| `test_views.py` | `PaymentSuccessViewTest` | Correct template rendering |
| `test_views.py` | `PaymentFailedViewTest` | Correct template rendering |
| `test_signals.py` | `PaypalIPNSignalTest` | Valid IPN creates transaction, receiver email mismatch, amount mismatch, currency mismatch, non-completed status |

Run tests:

```bash
make test
```
