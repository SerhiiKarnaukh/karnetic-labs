# Taberna eCommerce

### App on AWS: <https://karnetic-labs.com/taberna-store/>

![Taberna screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/portfolio/apps/taberna_product/taberna.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Apps & Models](#apps--models)
  - [taberna_product -- Product Catalog](#taberna_product----product-catalog)
  - [taberna_cart -- Shopping Cart](#taberna_cart----shopping-cart)
  - [taberna_orders -- Orders & Payments](#taberna_orders----orders--payments)
  - [taberna_profiles -- User Profiles](#taberna_profiles----user-profiles)
- [URL Routes](#url-routes)
- [REST API](#rest-api)
  - [Products API](#products-api)
  - [Cart API](#cart-api)
  - [Orders API](#orders-api)
  - [Profiles API](#profiles-api)
- [Payment Integrations](#payment-integrations)
- [Scheduled Tasks](#scheduled-tasks)
- [Frontend Development](#frontend-development)

---

## Overview

**Taberna** is a full-featured e-commerce module built on Django. It provides a product catalog with categories, variations (color/size), reviews and ratings, a shopping cart for both guest and authenticated users, order processing with Stripe and PayPal payments, and user profile management with email-based activation.

The module is composed of four tightly integrated Django apps that share models and utilities across boundaries.

---

## Architecture

```
taberna_profiles ─── accounts.Account (custom user model)
       │
       ▼
taberna_product ──── Category, Product, Variation, ReviewRating, ProductGallery
       │
       ▼
taberna_cart ──────── Cart, CartItem  (guest + authenticated)
       │
       ▼
taberna_orders ───── Order, Payment, OrderProduct  (Stripe / PayPal)
```

**Dependency chain:** `taberna_profiles` -> `taberna_product` -> `taberna_cart` -> `taberna_orders`

---

## Apps & Models

### taberna_product -- Product Catalog

See [taberna_product source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/taberna_product)

#### Models

| Model | Key Fields | Purpose |
|---|---|---|
| `Category` | name, slug, description, cat_image, ordering | Product categories |
| `Product` | name, slug, category (FK), created_by (FK -> UserProfile), price, stock, image, is_available, stripe_product_id | Product entry |
| `Variation` | product (FK), variation_category (color/size), variation_value, is_active | Product variants |
| `ReviewRating` | product (FK), user (FK -> UserProfile), subject, review, rating, ip, status | Customer reviews |
| `ProductGallery` | product (FK), image | Additional product images |

**Custom manager:** `VariationManager` with `colors()` and `sizes()` helper methods.

**Product methods:** `averageReview()`, `countReview()`, `get_absolute_url()`.

#### Views

| View | Type | Template | Description |
|---|---|---|---|
| `FrontPage` | ListView | `taberna_store/frontpage.html` | Landing page, first 6 products |
| `ProductDetail` | DetailView | `taberna_product/product_detail.html` | Product page with gallery, reviews, related products |
| `CategoryDetail` | ListView | `taberna_product/store.html` | Category listing (6 per page) or full store |
| `ProductSearchListView` | ListView | `taberna_product/store.html` | Search results (4 per page) |
| `contact` | Function | `taberna_store/contact.html` | Contact page |
| `about` | Function | `taberna_store/about.html` | About page |
| `submit_review` | Function | -- | Handles review create/update, redirects back |

#### Context Processors

- `menu_categories` -- all categories with at least one product (available in every template)
- `top_categories` -- top 6 categories with at least one product

#### Admin

Products admin includes inline `ProductGallery` (tabular with thumbnails) and inline `Variation` editing. Categories support drag-order via `list_editable` on the `ordering` field.

---

### taberna_cart -- Shopping Cart

See [taberna_cart source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/taberna_cart)

#### Models

| Model | Key Fields | Purpose |
|---|---|---|
| `Cart` | cart_id, date_added | Session-based cart container |
| `CartItem` | user (FK -> UserProfile, nullable), product (FK), variations (M2M -> Variation), cart (FK, nullable), quantity, is_active | Individual line item |

Guest users are tracked by session key; authenticated users are linked directly. On login, guest cart items are merged into the user's cart.

#### Views

| View | Type | Description |
|---|---|---|
| `cart` | Function | Displays cart page with totals |
| `add_cart` | Function | Adds product (with variations) to cart |
| `remove_cart` | Function | Decrements quantity or removes item |
| `remove_cart_item` | Function | Removes item entirely |
| `checkout` | Function | Checkout page (login required) |

#### Context Processors

- `counter` -- returns `cart_count` (total quantity) available in every template

#### Utility Functions

`utils.py` provides helpers for cart operations: `get_cart_id`, `get_product_variations`, `create_new_cart`, `get_or_create_cart`, `handle_cart_item`, `get_cart_items`, `calculate_cart_totals`, `prepare_cart_context`.

#### Celery Tasks

- `delete_old_carts` -- removes carts older than 60 days (runs daily at 03:00 UTC)

---

### taberna_orders -- Orders & Payments

See [taberna_orders source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/taberna_orders)

#### Models

| Model | Key Fields | Purpose |
|---|---|---|
| `Payment` | user (FK -> UserProfile), payment_id, payment_method, amount_paid, status | Payment record |
| `Order` | user (FK), payment (FK), order_number, first/last name, phone, email, address fields, order_total, tax, status, is_ordered, stripe_checkout_session_id | Customer order |
| `OrderProduct` | order (FK), payment (FK), user (FK), product (FK), variations (M2M), quantity, product_price, ordered | Ordered line item |

**Order statuses:** `New` -> `Accepted` -> `Completed` / `Cancelled`

#### Views

| View | Type | Description |
|---|---|---|
| `place_order` | Function | Creates order, renders PayPal payment form |
| `order_complete` | Function | Order success page |
| `order_failed` | Function | Order failure page |
| `stripe_webhook` | Function | Handles Stripe webhook events (CSRF exempt) |

#### Signals

- `paypal_taberna_payment_received` -- listens to `valid_ipn_received` from django-paypal. Processes IPN, creates payment record, updates order, creates order products, reduces stock, clears cart, and sends confirmation email.

#### Utility Functions

`utils.py` provides: `create_order_from_form`, `generate_order_number`, `create_payment`, `update_order`, `create_order_products`, `clear_cart`, `send_order_email`, `stripe_charge_create`, `get_tax_rate`, `stripe_session_create`.

#### App Startup

On app ready, creates a Stripe tax rate (VAT) if it does not already exist.

---

### taberna_profiles -- User Profiles

See [taberna_profiles source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/taberna_profiles)

#### Models

| Model | Key Fields | Purpose |
|---|---|---|
| `UserProfile` | user (OneToOne -> Account), address_line_1/2, profile_picture, city, state, country | E-commerce user profile |

#### Views

| View | Type | Description |
|---|---|---|
| `register` | Function | Registration with email activation |
| `login` | Function | Email-based login, merges guest cart |
| `logout` | Function | Logs out, redirects to login |
| `activate` | Function | Activates account via email token |
| `dashboard` | Function | User dashboard with recent orders |
| `my_orders` | Function | Full order history |
| `order_detail` | Function | Single order detail |
| `edit_profile` | Function | Edit user + profile info |
| `change_password` | Function | Change password (authenticated) |
| `forgotPassword` | Function | Password reset request |
| `resetPassword` | Function | Set new password via token |

#### Forms

| Form | Model | Fields |
|---|---|---|
| `RegistrationForm` | Account | first_name, last_name, phone_number, email, password |
| `UserForm` | Account | first_name, last_name, phone_number |
| `UserProfileForm` | UserProfile | address_line_1/2, city, state, country, profile_picture |

---

## URL Routes

All Taberna URLs are mounted under the following prefixes in the root `urls.py`:

| Prefix | App |
|---|---|
| `/taberna-store/` | taberna_product |
| `/taberna-cart/` | taberna_cart |
| `/taberna-orders/` | taberna_orders |
| `/taberna-profiles/` | taberna_profiles |

### taberna_product URLs

| Pattern | View | Name |
|---|---|---|
| `` | `FrontPage` | `frontpage` |
| `shop/` | `CategoryDetail` | `store` |
| `category/<slug>/` | `CategoryDetail` | `category_detail` |
| `category/<slug>/<slug>/` | `ProductDetail` | `product_detail` |
| `submit_review/<int>/` | `submit_review` | `submit_review` |
| `search/` | `ProductSearchListView` | `search` |
| `contact/` | `contact` | `contact` |
| `about/` | `about` | `about` |

### taberna_cart URLs

| Pattern | View | Name |
|---|---|---|
| `` | `cart` | `cart` |
| `add_cart/<int>/` | `add_cart` | `add_cart` |
| `remove_cart/<int>/<int>/` | `remove_cart` | `remove_cart` |
| `remove_cart_item/<int>/<int>/` | `remove_cart_item` | `remove_cart_item` |
| `checkout/` | `checkout` | `checkout` |

### taberna_orders URLs

| Pattern | View | Name |
|---|---|---|
| `place_order/` | `place_order` | `place_order` |
| `order_complete/<int>/` | `order_complete` | `order_complete` |
| `order_failed/` | `order_failed` | `order_failed` |
| `stripe_webhook/` | `stripe_webhook` | `stripe_webhook` |

### taberna_profiles URLs

| Pattern | View | Name |
|---|---|---|
| `` | `dashboard` | `dashboard` |
| `register/` | `register` | `register` |
| `login/` | `login` | `login` |
| `logout/` | `logout` | `logout` |
| `activate/<uidb64>/<token>/` | `activate` | `activate` |
| `activate-result/` | `activate_result` | `activate_result` |
| `dashboard/` | `dashboard` | `dashboard` |
| `forgot_password/` | `forgotPassword` | `forgotPassword` |
| `reset_password_validate/<uidb64>/<token>/` | `resetpassword_validate` | `resetpassword_validate` |
| `reset_password/` | `resetPassword` | `resetPassword` |
| `change_password/` | `change_password` | `change_password` |
| `my_orders/` | `my_orders` | `my_orders` |
| `edit_profile/` | `edit_profile` | `edit_profile` |
| `order_detail/<int>/` | `order_detail` | `order_detail` |

---

## REST API

![Taberna DRF screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/portfolio/apps/taberna_product/taberna_drf.jpg)

All API endpoints use Django REST Framework and return JSON.

### Products API

Base: `/taberna-store/api/`

| Method | Endpoint | View | Description |
|---|---|---|---|
| GET | `v1/latest-products/` | `LatestProductsAPIList` | First 6 available products (with Stripe ID) |
| GET | `v1/products/<category_slug>/<product_slug>/` | `ProductAPIDetail` | Product detail with reviews, variations, related products |
| GET | `v1/products/<category_slug>/` | `CategoryAPIDetail` | Category with its products |
| GET | `v1/product-categories/` | `ProductCategoryAPIView` | All non-empty categories |
| POST | `v1/products/search/` | `search_api` | Search products by name/description. Body: `{"query": "..."}` |

**Serializers:**
- `ProductSerializer` -- id, name, image, description, price, get_absolute_url, productgallery (nested)
- `ProductGallerySerializer` -- id, image
- `ReviewRatingSerializer` -- id, user, subject, review, rating, created_at, updated_at
- `CategorySerializer` -- id, name, get_absolute_url, products (filtered by Stripe ID)
- `AllCategoriesSerializer` -- id, name, get_absolute_url
- `VariationSerializer` -- id, variation_category, variation_value

### Cart API

Base: `/taberna-cart/api/`

| Method | Endpoint | View | Description |
|---|---|---|---|
| GET | `cart/` | `CartAPIView` | Cart items, totals, tax, grand total |
| POST | `add-to-cart/<product_id>/` | `AddToCartView` | Add product to cart. Body: `{"variations": [...], "cart_id": "..."}` |
| DELETE | `cart-remove/<product_id>/<cart_item_id>/` | `RemoveCartItemAPIView` | Decrement quantity or remove item |
| DELETE | `cart-item-remove/<product_id>/<cart_item_id>/` | `RemoveCartItemFullyAPIView` | Remove item entirely |

**Serializers:**
- `CartItemSerializer` -- id, product (nested), variations (nested), quantity, is_active, sub_total

### Orders API

Base: `/taberna-orders/api/`

| Method | Endpoint | Auth | View | Description |
|---|---|---|---|---|
| POST | `v1/place_order_stripe_charge/` | Required | `PlaceOrderStripeChargeAPIView` | Create order + immediate Stripe charge |
| POST | `v1/place_order_stripe_session/` | Required | `PlaceOrderStripeSessionAPIView` | Create Stripe checkout session, returns `checkout_url` |
| POST | `v1/order_payment_success/` | -- | `OrderPaymentSuccessAPIView` | Process order after successful Stripe payment (DEBUG only) |
| POST | `v1/order_payment_failed/` | -- | `OrderPaymentFailedAPIView` | Delete order on payment failure |

**Serializers:**
- `PaymentSerializer` -- payment_id, payment_method, amount_paid, status, created_at
- `OrderProductSerializer` -- id, product (nested), variations (nested), quantity, product_price, ordered
- `OrderSerializer` -- id, order_number, names, address, totals, status, payment (nested), order_products (nested)

### Profiles API

Base: `/taberna-profiles/api/`

| Method | Endpoint | Auth | View | Description |
|---|---|---|---|---|
| POST | `register/` | -- | `TabernaProfileCreateView` | Register user + create profile, sends activation email |
| POST | `v1/token/` | -- | `CustomTokenObtainPairView` | JWT login (merges guest cart on success) |
| GET | `v1/orders/` | Required | `UserOrdersListView` | List authenticated user's completed orders |

---

## Payment Integrations

### Stripe

- **Charge API** -- immediate payment via `PlaceOrderStripeChargeAPIView`
- **Checkout Sessions** -- redirect-based flow via `PlaceOrderStripeSessionAPIView`
- **Webhooks** -- `stripe_webhook` view handles `checkout.session.completed` events
- **Tax rates** -- VAT tax rate is auto-created on app startup
- Products can be linked via `stripe_product_id` field

### PayPal

- **Standard IPN** -- handled via `django-paypal` signal `valid_ipn_received`
- Payment form rendered on the `place_order` page
- Sandbox mode controlled by `PAYPAL_TEST` env variable

---

## Scheduled Tasks

| Time (UTC) | Task | App | Description |
|---|---|---|---|
| 03:00 | `delete_old_carts` | taberna_cart | Removes carts older than 60 days |

---

## Frontend Development

The product catalog frontend is built with Webpack. Source is located in `portfolio/apps/taberna_product/_dev/`.

See [Taberna eCommerce Frontend](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/taberna_product/_dev)

**Tech stack:** Bootstrap 5.3.8, jQuery 4.0.0, AOS (animations), Swiper (carousel), SCSS

**Build output:** `../static/taberna_product/bundle/`

### Commands

```bash
nvm use 22.19.0
cd portfolio/apps/taberna_product/_dev
npm install
npm run w     # Watch mode (development)
npm run b     # Production build
npm run d     # Development build
```

Or via Makefile from the project root:

```bash
make update_front_taberna
```
