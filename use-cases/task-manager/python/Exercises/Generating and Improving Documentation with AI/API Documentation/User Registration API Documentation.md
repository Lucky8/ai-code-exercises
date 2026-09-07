# User Registration API Documentation

## Endpoint Overview

### Basic Information
- **HTTP Method:** `POST`
- **Endpoint Path:** `/api/users/register`
- **Description:** Registers a new user in the system and sends a confirmation email
- **Authentication:** Not required (public endpoint)
- **Content-Type:** `application/json`

---

## Purpose

This endpoint allows new users to create an account in the system. It handles user registration with comprehensive validation, including duplicate checking, email format validation, and password strength requirements. Upon successful registration, a confirmation email is sent to the user's email address.

---

## Request

### Request Body

The endpoint accepts a JSON payload with the following required fields:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `username` | String | Yes | The desired username for the account | Must be unique; no length restrictions specified in code |
| `email` | String | Yes | User's email address | Must be unique; must match format `*@*.* ` |
| `password` | String | Yes | User's password | Minimum 8 characters; case-sensitive |

### Request Headers

```
Content-Type: application/json
```

### Request Example 1: Successful Registration

```http
POST /api/users/register HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

### Request Example 2: Alternative Valid Request

```http
POST /api/users/register HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "username": "alice_smith",
  "email": "alice.smith@domain.co.uk",
  "password": "MyP@ssw0rd2024"
}
```

---

## Response

### Success Response (201 Created)

**Status Code:** `201 Created`

The user is successfully registered. A confirmation email has been sent (or attempted to be sent).

#### Response Body Schema

| Field | Type | Description |
|-------|------|-------------|
| `message` | String | Confirmation message indicating successful registration |
| `user` | Object | User object containing registration details |
| `user.id` | Integer | Unique identifier for the newly created user |
| `user.username` | String | The registered username |
| `user.email` | String | The registered email address |
| `user.created_at` | String (ISO 8601) | Timestamp of account creation in UTC |
| `user.role` | String | Default user role (typically "user") |

#### Success Response Example 1

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2026-09-07T14:30:45.123456",
    "role": "user"
  }
}
```

#### Success Response Example 2

```json
{
  "message": "User registered successfully",
  "user": {
    "id": 43,
    "username": "alice_smith",
    "email": "alice.smith@domain.co.uk",
    "created_at": "2026-09-07T15:45:22.654321",
    "role": "user"
  }
}
```

---

## Error Responses

### 400 Bad Request

Returned when the request is malformed or validation fails.

#### Missing Required Field (400)

**Condition:** A required field is missing from the request body.

**Status Code:** `400 Bad Request`

```json
{
  "error": "Missing required field",
  "message": "username is required"
}
```

Possible missing fields:
- `username`
- `email`
- `password`

#### Invalid Email Format (400)

**Condition:** Email does not match the required format.

**Status Code:** `400 Bad Request`

**Validation Rule:** Email must contain exactly one `@` symbol and at least one `.` after it (pattern: `^[^@]+@[^@]+\.[^@]+$`)

```json
{
  "error": "Invalid email",
  "message": "Please provide a valid email address"
}
```

**Example Invalid Emails:**
- `invalidemail`
- `user@`
- `@example.com`
- `user@example`

#### Weak Password (400)

**Condition:** Password does not meet minimum strength requirements.

**Status Code:** `400 Bad Request`

**Validation Rule:** Password must be at least 8 characters long.

```json
{
  "error": "Weak password",
  "message": "Password must be at least 8 characters long"
}
```

---

### 409 Conflict

Returned when the requested resource already exists.

#### Username Already Taken (409)

**Condition:** The provided username is already registered in the system.

**Status Code:** `409 Conflict`

```json
{
  "error": "Username taken",
  "message": "Username is already in use"
}
```

#### Email Already Exists (409)

**Condition:** An account with the provided email address already exists.

**Status Code:** `409 Conflict`

```json
{
  "error": "Email exists",
  "message": "An account with this email already exists"
}
```

---

### 500 Internal Server Error

Returned when an unexpected server-side error occurs during registration.

**Condition:** An exception occurs during user creation, database operations, or email sending (after validation passes).

**Status Code:** `500 Internal Server Error`

```json
{
  "error": "Server error",
  "message": "Failed to register user"
}
```

**Note:** The actual error details are logged server-side but not exposed to the client for security reasons. Email sending failures are logged but do not prevent successful registration.

---

## Response Status Code Summary

| Status Code | Meaning | Cause |
|-------------|---------|-------|
| 201 | Created | User successfully registered |
| 400 | Bad Request | Missing fields, invalid email format, or weak password |
| 409 | Conflict | Username or email already exists |
| 500 | Internal Server Error | Database or server error |

---

## Complete Request/Response Flow Examples

### Example 1: Successful Registration

**Request:**
```bash
curl -X POST https://api.example.com/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alex_johnson",
    "email": "alex.johnson@company.com",
    "password": "SecureP@ss123"
  }'
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 101,
    "username": "alex_johnson",
    "email": "alex.johnson@company.com",
    "created_at": "2026-09-07T10:15:30.456789",
    "role": "user"
  }
}
```

**Post-Registration Actions:**
- Confirmation email sent to `alex.johnson@company.com`
- User account created with role `user`
- Password securely hashed using industry-standard algorithm

### Example 2: Duplicate Email Error

**Request:**
```bash
curl -X POST https://api.example.com/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "existing.user@company.com",
    "password": "ValidPassword123"
  }'
```

**Response (409):**
```json
{
  "error": "Email exists",
  "message": "An account with this email already exists"
}
```

**Suggested Next Steps:**
- User should use a different email address
- Or use "Forgot Password" feature if they already have an account with that email

---

## Authentication & Security

### Authentication Requirements
- **None required** for this endpoint (public registration)
- This is an unauthenticated endpoint that allows any client to create an account

### Security Measures Implemented

1. **Password Hashing:** Passwords are hashed using a secure algorithm (bcrypt/werkzeug) before storage
2. **Email Validation:** Email format is validated against a regex pattern
3. **Duplicate Prevention:** Username and email uniqueness checks prevent duplicate accounts
4. **Password Strength:** Minimum 8-character requirement enforces baseline password complexity
5. **Data Sanitization:** Email is normalized to lowercase before storage
6. **Error Handling:** Sensitive error details are not exposed to clients; detailed logs are server-side only
7. **Email Confirmation:** Confirmation token sent via email for account verification (post-registration)

### Recommended Security Practices for Clients

1. Use HTTPS/TLS for all requests (encrypt data in transit)
2. Enforce strong password requirements on the client side
3. Implement rate limiting on the client to prevent brute force attempts
4. Sanitize user input before sending to the API
5. Store user credentials securely and never transmit them unnecessarily

---

## Rate Limiting

### Rate Limit Policy

**Current Status:** Not explicitly enforced at the endpoint level in the provided code.

**Recommended Implementation:**
- **Limit:** 5 registration attempts per IP address per 15 minutes
- **Limit:** 10 registration attempts per email address per hour
- **Response Header:** Include `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- **Throttle Response (429):** Return `429 Too Many Requests` when limits are exceeded

### Purpose
- Prevent abuse and spam account creation
- Reduce database load from malicious registration attempts
- Protect against automated account harvesting

---

## Additional Considerations

### Email Confirmation Flow

After successful registration:
1. A confirmation token is generated using the new user's ID
2. Confirmation email is sent asynchronously to the registered email address
3. If email sending fails, the operation continues (user account is created but unconfirmed)
4. Failure to send email is logged server-side but does not affect the HTTP response
5. Users should check their spam/junk folder if confirmation email is not received

### Database Transactions

- User registration is wrapped in a database transaction
- On error, the transaction is automatically rolled back
- Ensures data consistency if an error occurs after user creation

### Input Normalization

- **Email:** Converted to lowercase before storage for case-insensitive uniqueness
- **Username:** Stored as provided (case-sensitive)
- **Password:** Hashed immediately before storage; original password never persisted

### Default User Settings

- **Role:** All new users are assigned `role: "user"` by default
- **Created At:** Set to UTC timestamp at account creation time
- **Status:** Assumed to be unconfirmed until email confirmation link is used

---

## Related Endpoints

- `POST /api/users/confirm` - Confirm user email address (uses confirmation token)
- `POST /api/users/login` - Authenticate and receive session/JWT token
- `POST /api/users/forgot-password` - Request password reset
- `POST /api/users/resend-confirmation` - Resend confirmation email

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-09-07 | Initial documentation |

---

## Support & Questions

For issues or questions regarding this endpoint, please:
1. Check the troubleshooting section above
2. Review the error message and status code
3. Contact the development team with the full request and response details
