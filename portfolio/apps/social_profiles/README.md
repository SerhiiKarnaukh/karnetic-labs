# Social Network DRF

### App on AWS: <https://django.karnaukh-webdev.com/category/django/social-network-drf/>

### App on Firebase: <https://karnaukh-vue-test.web.app/social/home>

![Social Network screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/portfolio/apps/social_profiles/social_network_main.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Apps & Models](#apps--models)
  - [social_profiles -- Profiles & Friends](#social_profiles----profiles--friends)
  - [social_posts -- Feed & Trends](#social_posts----feed--trends)
  - [social_chat -- Real-Time Chat](#social_chat----real-time-chat)
  - [social_notification -- Notifications](#social_notification----notifications)
- [REST API](#rest-api)
  - [Profiles API](#profiles-api)
  - [Posts API](#posts-api)
  - [Chat API](#chat-api)
  - [Notifications API](#notifications-api)
- [WebSocket Consumers](#websocket-consumers)
- [Scheduled Tasks](#scheduled-tasks)
- [Frontend](#frontend)
- [Testing](#testing)

---

## Overview

**Social Network** is a real-time social platform module built with Django REST Framework, Django Channels, and WebSockets. It provides user profiles with a friend system, a post feed with likes/comments/hashtags/trends, real-time private chat, and push notifications -- all exposed as a REST + WebSocket API consumed by a Vue.js frontend.

The module is composed of four Django apps that share `Profile` as the central user entity.

---

## Architecture

```
accounts.Account (custom user model)
       │
       ▼
social_profiles ──── Profile, FriendshipRequest
       │
       ├──────────────────────────────┐
       ▼                              ▼
social_posts                   social_chat
  Post, Like, Comment,           Conversation,
  PostAttachment, Trend          ConversationMessage
       │                              │
       └──────────┬───────────────────┘
                  ▼
       social_notification
         Notification (real-time via WebSocket)
```

**Dependency chain:** All apps depend on `social_profiles.Profile`. Notifications reference both posts and chat messages.

**Protocols:**
- **HTTP** -- REST API for CRUD operations (Django REST Framework + JWT)
- **WebSocket** -- real-time chat messages and push notifications (Django Channels + Redis)

---

## Apps & Models

### social_profiles -- Profiles & Friends

See [social_profiles source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/social_profiles)

#### Models

**Profile**

| Field | Type | Details |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `user` | OneToOneField -> Account | CASCADE |
| `first_name` | CharField(200) | blank=True |
| `last_name` | CharField(200) | blank=True |
| `username` | CharField(50) | unique |
| `email` | EmailField(200) | blank=True |
| `bio` | TextField(300) | default="no bio..." |
| `country` | CharField(200) | blank=True |
| `avatar` | ImageField | upload_to='social/avatars/' |
| `friends` | ManyToManyField('self') | Symmetric friendship |
| `friends_count` | IntegerField | default=0 |
| `people_you_may_know` | ManyToManyField('self') | Friend suggestions |
| `posts_count` | IntegerField | default=0 |
| `slug` | SlugField | unique, auto-generated |
| `created` | DateTimeField | auto_now_add |
| `updated` | DateTimeField | auto_now |

Methods: `full_name()`, `create_slug()`. The `save()` override syncs first/last name with the Account model and auto-generates the slug.

**FriendshipRequest**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `created_by` | ForeignKey -> Profile | related_name='created_friendshiprequests' |
| `created_for` | ForeignKey -> Profile | related_name='received_friendshiprequests' |
| `status` | CharField(20) | Choices: `sent`, `accepted`, `rejected` |
| `created_at` | DateTimeField | auto_now_add |

#### Signals

- **pre_save** on Profile -- deletes old avatar file from disk when the avatar is changed.

#### Celery Tasks

| Task | Schedule | Description |
|---|---|---|
| `create_social_friend_suggestions` | Daily 05:00 UTC | Populates `people_you_may_know` based on friends-of-friends |
| `delete_old_rejected_friendship_requests` | Daily 04:30 UTC | Deletes rejected requests older than 7 days |

---

### social_posts -- Feed & Trends

See [social_posts source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/social_posts)

#### Models

**Post**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `body` | TextField | blank=True, null=True |
| `attachments` | ManyToManyField -> PostAttachment | blank=True |
| `is_private` | BooleanField | default=False |
| `likes` | ManyToManyField -> Like | blank=True |
| `likes_count` | IntegerField | default=0 |
| `comments` | ManyToManyField -> Comment | blank=True |
| `comments_count` | IntegerField | default=0 |
| `reported_by_users` | ManyToManyField -> Profile | blank=True |
| `created_by` | ForeignKey -> Profile | related_name='posts' |
| `created_at` | DateTimeField | auto_now_add |

Ordering: `-created_at`. Method: `created_at_formatted()` (timesince).

**Like**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `created_by` | ForeignKey -> Profile | related_name='likes' |
| `created_at` | DateTimeField | auto_now_add |

**Comment**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `body` | TextField | blank=True, null=True |
| `created_by` | ForeignKey -> Profile | related_name='comments' |
| `created_at` | DateTimeField | auto_now_add |

Ordering: `created_at`. Method: `created_at_formatted()`.

**PostAttachment**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `image` | ImageField | upload_to='social/posts', validates png/jpg/jpeg |
| `created_by` | ForeignKey -> Profile | related_name='post_attachments' |

**Trend**

| Field | Type | Details |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `hashtag` | CharField(255) | Extracted hashtag |
| `occurences` | IntegerField | Count of posts containing this hashtag |

#### Forms

| Form | Model | Fields | Validation |
|---|---|---|---|
| `PostForm` | Post | body, is_private | Body min length 3 |
| `AttachmentForm` | PostAttachment | image | -- |

#### Pagination

`PostPagination` -- PageNumberPagination, page_size=3, max_page_size=100.

#### Utility Functions

- `get_trending_posts(trend)` -- returns posts matching a hashtag pattern
- `get_user_feed_posts(user)` -- returns own + friends' posts for authenticated users, or public posts for guests

#### Celery Tasks

| Task | Schedule | Description |
|---|---|---|
| `create_social_posts_trends` | Daily 04:00 UTC | Analyzes posts from last 24h, extracts hashtags, creates top 10 Trend entries |

---

### social_chat -- Real-Time Chat

See [social_chat source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/social_chat)

#### Models

**Conversation**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `users` | ManyToManyField -> Profile | related_name='conversations' |
| `created_at` | DateTimeField | auto_now_add |
| `modified_at` | DateTimeField | auto_now |

Method: `modified_at_formatted()`.

**ConversationMessage**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `conversation` | ForeignKey -> Conversation | related_name='messages' |
| `body` | TextField | Message content |
| `created_by` | ForeignKey -> Profile | related_name='sent_messages' |
| `sent_to` | ForeignKey -> Profile | related_name='received_messages' |
| `created_at` | DateTimeField | auto_now_add |

Method: `created_at_formatted()`.

#### WebSocket Consumer

**`SocialChatConsumer`** (AsyncWebsocketConsumer)

| Event | Action |
|---|---|
| `connect()` | Joins channel group `social_chat_{conversation_id}` |
| `disconnect()` | Leaves channel group |
| `send_message(event)` | Pushes message JSON to WebSocket client |

WebSocket URL: `ws/social-chat/<conversation_id>/<user_id>/` (also `wss/` variant)

Messages are persisted via the REST API (`conversation_send_message`) and then broadcast to the channel group.

---

### social_notification -- Notifications

See [social_notification source](https://github.com/SerhiiKarnaukh/karnetic-labs/tree/main/portfolio/apps/social_notification)

#### Model

**Notification**

| Field | Type | Details |
|---|---|---|
| `id` | UUIDField | Primary key |
| `body` | TextField | Notification message |
| `is_read` | BooleanField | default=False |
| `type_of_notification` | CharField(50) | See choices below |
| `post` | ForeignKey -> Post | nullable, CASCADE |
| `created_by` | ForeignKey -> Profile | related_name='created_notifications' |
| `created_for` | ForeignKey -> Profile | related_name='received_notifications' |
| `created_at` | DateTimeField | auto_now_add |

**Notification types:**

| Constant | Value | Trigger |
|---|---|---|
| `NEWFRIENDREQUEST` | new_friendrequest | Friend request sent |
| `ACCEPTEDFRIENDREQUEST` | accepted_friendrequest | Friend request accepted |
| `REJECTEDFRIENDREQUEST` | rejected_friendrequest | Friend request rejected |
| `POST_LIKE` | post_like | Post liked |
| `POST_COMMENT` | post_comment | Comment added |
| `CHAT_MESSAGE` | chat_message | Chat message received |

#### WebSocket Consumer

**`NotificationConsumer`** (AsyncWebsocketConsumer)

| Event | Action |
|---|---|
| `connect()` | Joins channel group `notifications_{user_id}` |
| `disconnect()` | Leaves channel group |
| `send_notification(event)` | Pushes notification JSON to WebSocket client |

WebSocket URL: `ws/notification/<user_id>/` (also `wss/` variant)

#### Utility Functions

- `send_notification(account, message)` -- sends a WebSocket push to the user's notification group
- `create_notification(request, type_of_notification, post_id, friendrequest_id, conversation_message_id)` -- creates a `Notification` record and triggers a WebSocket push based on the notification type

---

## REST API

All endpoints require JWT authentication unless noted otherwise. Responses are JSON.

### Profiles API

Base: `/api/social-profiles/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `register/` | -- | Create account + profile, sends activation email |
| GET | `me/` | Required | Current user's profile |
| POST | `editprofile/` | Required | Update profile (first_name, last_name, username, email, avatar) |
| POST | `editpassword/` | Required | Change password |
| GET | `friends/<slug>/` | Required | User's friends list + pending requests sent to current user |
| POST | `friends/<slug>/request/` | Required | Send friendship request |
| POST | `friends/<slug>/<status>/` | Required | Accept or reject friendship request (`accepted` / `rejected`) |
| GET | `friends/suggested/` | Required | Friend suggestions |

**Serializers:**
- `ProfileSerializer` -- id, first_name, last_name, username, email, slug, avatar_url, friends_count, posts_count, full_name
- `FriendshipRequestSerializer` -- id, created_by (nested ProfileSerializer)

### Posts API

Base: `/api/social-posts/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `` | Optional | Paginated feed (trending posts by hashtag via `?trend=` or user feed) |
| GET | `<uuid:pk>/` | Optional | Single post with comments |
| GET | `profile/<slug>/` | Optional | Posts by a specific user |
| POST | `create/` | Required | Create post with optional image attachments |
| POST | `<uuid:pk>/like/` | Required | Toggle like on post (creates notification) |
| POST | `<uuid:pk>/comment/` | Required | Add comment to post (creates notification) |
| DELETE | `<uuid:pk>/delete/` | Required | Delete own post |
| POST | `<uuid:pk>/report/` | Required | Report a post |
| POST | `search/` | Optional | Search profiles and posts by query |
| GET | `trends/` | Optional | Top 10 trending hashtags |

**Serializers:**
- `PostSerializer` -- id, body, is_private, likes_count, comments_count, created_by (nested), created_at_formatted, attachments (nested)
- `PostDetailSerializer` -- same as PostSerializer + comments (nested)
- `CommentSerializer` -- id, body, created_by (nested), created_at_formatted
- `PostAttachmentSerializer` -- id, image_url
- `TrendSerializer` -- id, hashtag, occurences

### Chat API

Base: `/api/social-chat/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `` | Required | List user's conversations |
| GET | `<uuid:pk>/` | Required | Conversation detail with messages |
| GET | `<slug>/get-or-create/` | Required | Get existing or create new conversation with user |
| POST | `<uuid:pk>/send/` | Required | Send message (persists + broadcasts via WebSocket, creates notification) |

**Serializers:**
- `ConversationSerializer` -- id, users (nested ProfileSerializer), modified_at_formatted
- `ConversationDetailSerializer` -- same + messages (nested)
- `ConversationMessageSerializer` -- id, body, sent_to (nested), created_by (nested), created_at_formatted

### Notifications API

Base: `/api/social-notifications/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `` | Required | List unread notifications |
| POST | `read/<uuid:pk>/` | Required | Mark notification as read |

**Serializers:**
- `NotificationSerializer` -- id, body, type_of_notification, post_id, created_for_id

---

## WebSocket Consumers

Both consumers use Django Channels with Redis as the channel layer. Authentication is handled by `AuthMiddlewareStack` in `asgi.py`.

| Consumer | WebSocket URL | Channel Group | Purpose |
|---|---|---|---|
| `SocialChatConsumer` | `ws(s)/social-chat/<conversation_id>/<user_id>/` | `social_chat_{conversation_id}` | Real-time chat messages |
| `NotificationConsumer` | `ws(s)/notification/<user_id>/` | `notifications_{user_id}` | Real-time push notifications |

**Flow (chat example):**
1. Client connects to `ws/social-chat/{conv_id}/{user_id}/`
2. Consumer joins the `social_chat_{conv_id}` channel group
3. Client sends a message via REST API (`POST /api/social-chat/{conv_id}/send/`)
4. The API view persists the message, then broadcasts to the channel group
5. All connected clients in the conversation receive the message in real-time

---

## Scheduled Tasks

| Time (UTC) | Task | App | Description |
|---|---|---|---|
| 04:00 | `create_social_posts_trends` | social_posts | Extracts hashtags from last 24h posts, saves top 10 as Trend entries |
| 04:30 | `delete_old_rejected_friendship_requests` | social_profiles | Deletes rejected friend requests older than 7 days |
| 05:00 | `create_social_friend_suggestions` | social_profiles | Populates `people_you_may_know` from friends-of-friends |

---

## Frontend

The Social Network frontend is a separate **Vue.js** application deployed on Firebase.

- **Vue.js frontend**: <https://karnaukh-vue-test.web.app/social/home>
- **Project page**: <https://django.karnaukh-webdev.com/category/vuejs/social-network-vuejs/>

The frontend consumes the REST API via JWT authentication and connects to WebSocket endpoints for real-time chat and notifications.

---

## Testing

Tests are located in each app's `tests/` directory or `test_*.py` files:

| App | Test Files | Coverage |
|---|---|---|
| social_posts | `test_api.py`, `test_serializers.py`, `test_utils.py` | Post CRUD, feed, search, likes, comments, trends, attachments |
| social_chat | `test_api.py` | Conversation list, detail, get-or-create, send message |
| social_notification | `test_api.py`, `test_utils.py` | Notification list, read, create for all 6 notification types |
| social_profiles | `tests.py` | Placeholder |

Run tests:

```bash
make test
```
