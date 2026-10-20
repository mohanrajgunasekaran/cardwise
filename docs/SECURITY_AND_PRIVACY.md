# CardWise Security and Privacy Architecture

## 1. Core Security Principles

### 1.1 Zero High-Risk Credential Policy
CardWise is architected as an informational personal finance manager. Under no circumstances does the application ask for, accept, transmit, process, or store:
- Full 16-digit Primary Account Numbers (PANs).
- Card Verification Values (CVV/CVC/CID).
- Personal Identification Numbers (PINs).
- Net banking passwords or secondary credentials.
- One-Time Passwords (OTPs) or transaction authorization codes.

Cards are stored using masked representations only (e.g., `XXXX-XXXX-XXXX-7207`).

---

## 2. Android Client-Side Security

1. **Android Keystore Backing**:
   - Authentication tokens and session identifiers are stored in `EncryptedSharedPreferences` utilizing an AES-256-GCM master key protected by the hardware-backed Android Keystore.
2. **Network Security Configuration**:
   - Enforce HTTPS and TLS 1.3 exclusively (`cleartextTrafficPermitted="false"` in `network_security_config.xml`).
   - Certificate pinning option for production API hosts.
3. **Screen Security & Leak Prevention**:
   - `FLAG_SECURE` enabled on sensitive screens to prevent unauthorized screenshots and display preview caching in the Android Recent Apps switcher.
4. **No Sensitive Telemetry**:
   - Financial balances, masked card numbers, or transaction details are explicitly filtered out from logcat statements and any third-party crash reporting.

---

## 3. Backend API Security

1. **Strict Ownership Enforcement**:
   - Cross-user data leaks are prevented at the database query layer. Every read and write query enforces `WHERE user_id = :auth_user_id`.
   - Never trust client-supplied user identifiers in payloads.
2. **Authentication & Token Lifecycle**:
   - Passwords hashed using `bcrypt` with salt rounds >= 12.
   - Access tokens are short-lived (15 minutes), signed with HMAC-SHA256.
   - Refresh tokens (7 days) are rotatable and revocable.
3. **Input Sanitization**:
   - Pydantic v2 schemas reject unexpected fields (`extra = "forbid"`).
   - SQL injection prevention via SQLAlchemy parameterized statements.
4. **Rate Limiting**:
   - Authentication and sensitive calculation endpoints are throttled to mitigate brute-force attempts.

---

## 4. Privacy & Compliance

1. **Data Minimization**: Only information essential for calculating reward benefits and payment tracking is collected.
2. **User Data Rights**:
   - Complete export workflow (`GET /api/v1/auth/export-data`).
   - Irreversible account deletion workflow (`DELETE /api/v1/auth/account`).
