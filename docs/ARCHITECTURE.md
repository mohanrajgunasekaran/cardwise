# CardWise System Architecture

## 1. High-Level Architecture

The CardWise platform utilizes an **Offline-First Clean Architecture** on Android backed by a **Stateless Modular REST API** on FastAPI with PostgreSQL.

```
                      +------------------------------------------+
                      |         CardWise Android App             |
                      |  (Kotlin, Jetpack Compose, Material 3)   |
                      +--------------------+---------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
         [UI Layer: Jetpack Compose]                    [Background Work]
         - Screens & Components                         - WorkManager Worker
         - ViewModels & UI States                       - Local Notification Engine
                   |                                               |
         [Domain Layer]                                            |
         - Financial Math Engine (Decimal)                         |
         - Smart Card Matcher Logic                                |
         - Validation & Formatting                                 |
                   |                                               |
         [Data Layer / Repository]                                 |
         - CardWiseRepository                                      |
         +-----------------+-------------------+                   |
         |                 |                   |                   |
    [Room SQLite]    [Android Keystore]  [Retrofit HTTP Client]    |
    - Local Cache    - Encrypted Token   - API Communication       |
         |                                     |                   |
         +-------------------------------------+-------------------+
                                               |
                                     (HTTPS / JSON REST API)
                                               |
                      +------------------------v-----------------+
                      |           FastAPI Backend Engine          |
                      |  - JWT Auth Guard                        |
                      |  - Pydantic v2 Request Validation        |
                      |  - Financial Matcher Service             |
                      |  - Statement Processing & Audit Log      |
                      +------------------------+-----------------+
                                               |
                                       [SQLAlchemy 2.0]
                                               |
                               +---------------+---------------+
                               |                               |
                     [PostgreSQL (Prod)]             [SQLite (Dev/Test)]
```

---

## 2. Android Architecture (MVVM + Clean Architecture)

### 2.1 Layer Separation
- **Presentation Layer**:
  - Jetpack Compose single-activity model (`MainActivity`).
  - Navigation Compose graph with typed routes.
  - State hoisting: Stateless Composables + Stateful `ViewModel` exposing `StateFlow<UiState>`.
- **Domain Layer**:
  - Pure Kotlin logic without Android framework dependencies.
  - `CardMatcherEngine`: Pure deterministic functions evaluating rules against purchase contexts.
  - `PaymentPlanCalculator`: Decimal-safe ledger arithmetic.
- **Data Layer**:
  - `RoomDatabase` (`CardWiseDatabase`): SQLite persistence for Cards, Statements, Payments, Offers, and Synced State.
  - `SecurityStorage`: Uses AndroidX `EncryptedSharedPreferences` / `MasterKeys` from Android Keystore.
  - `NetworkDataSource`: Retrofit + OkHttp with Token Authenticator for silent refresh.

---

## 3. Backend Architecture (FastAPI + SQLAlchemy)

### 3.1 Layer Separation
- **API Routers (`api/v1/`)**:
  - `/auth`: Login, registration, token refresh, biometric session exchange.
  - `/cards`: Card CRUD, verification status updates.
  - `/statements`: Statement tracking, duplicate detection, payment dues.
  - `/payments`: Planned and confirmed payment records.
  - `/matcher`: Smart recommendation engine API (server-side cross-validation).
  - `/offers`: Curated credit card offers and reward catalogs.
- **Core Services (`services/`)**:
  - `auth_service.py`: Password hashing with bcrypt, JWT creation, token blacklisting.
  - `matching_engine.py`: Category, merchant, and cap evaluation algorithms.
  - `financial_calculator.py`: Decimal ledger reconciliation.
- **Persistence (`models/` & `db/`)**:
  - Declarative SQLAlchemy models.
  - Alembic migrations for forward/backward schema updates.

---

## 4. Security & Data Isolation Architecture

1. **User Identity Boundary**: Every database query filters by `user_id` derived directly from the verified JWT `sub` claim. Client-provided `user_id` parameters are never trusted.
2. **Non-custodial Financial Security**: No credentials, OTPs, CVVs, or full PANs are collected, processed, or persisted.
3. **Defense in Depth**:
   - Client: Keystore encryption for tokens, root detection warnings, masked UI display.
   - Network: TLS 1.3, HSTS headers, CORS origin restrictions.
   - Server: Strict Pydantic input sanitization, parameterized queries (SQLAlchemy), bcrypt password hashing, rate limiting on sensitive endpoints.
