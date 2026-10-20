# CardWise — Credit Card Benefits & Payment Manager

CardWise is a production-oriented personal finance management application tailored for Indian credit card holders. It simplifies multiple card statement cycles, optimizes reward point earnings, prevents accidental late interest charges, and maintains payment disbursements — all while upholding a **Zero High-Risk Credential Policy**.

---

## 🚀 Key Highlights & Architectural Pillars

1. **Zero Credential Exposure**:
   - Never requests, stores, or transmits full 16-digit card numbers, CVVs, PINs, OTPs, or bank passwords.
   - Cards are identified by masked numbers (e.g. `XXXX-XXXX-XXXX-7207`).
2. **Transparent Mathematical Engines**:
   - Strict decimal arithmetic (`BigDecimal` on Android, Python `Decimal` on backend). Floating-point math is strictly forbidden.
   - Transparent, explainable calculations for cashback, reward point multipliers, and spend caps.
3. **Offline-First & Keystore Protection**:
   - Room SQLite database on Android serves as the single source of truth for all local UI screens.
   - Android Keystore AES-256-GCM hardware protection for local session tokens and keys.
4. **Curated Reference Card Fixtures**:
   - Includes synthetic test fixtures for the 10 target cards:
     1. YES BANK ACE
     2. ICICI Bank Coral
     3. Amazon Pay ICICI Bank
     4. HDFC Bank credit card (Variant unknown, unverified)
     5. RBL Bank Shoprite
     6. AU Small Finance Bank LIT
     7. IndusInd Bank ending 7207
     8. IndusInd Bank ending 8377
     9. IDFC FIRST Bank LIC Select
     10. RBL Bank LazyPay

---

## 📱 Android Application (Kotlin + Jetpack Compose)

### Tech Stack
- **Language**: Kotlin 2.0+
- **UI System**: 100% Jetpack Compose with Material 3 Design (Bespoke Emerald/Teal & Slate theme — zero violet/purple)
- **Architecture**: MVVM with Clean Architecture separation
- **Persistence**: AndroidX Room Database with Kotlin Coroutines & Flow
- **Background Tasks**: Android WorkManager for periodic bill due date reminders and notification dispatch
- **Navigation**: Navigation Compose with typed routes

### Primary Destinations
1. **Home**: Live financial overview, aggregated statement balances, upcoming deadlines, overdue notices, planned vs confirmed disbursements.
2. **My Cards**: Card wallet displaying credit limits, available limits, billing day, reward types, and demo seed tools.
3. **Card Matcher**: Smart recommendation engine ranking cards by estimated net monetary benefit in ₹ with full calculation breakdowns.
4. **Payments**: Statement ledger reconciliation, multi-part planned disbursements, and user-confirmed status tracking.
5. **Rewards**: Curated offers catalog, category multipliers, and validity tracker.
6. **Settings**: Security details, notification toggles, and data export.
7. **Statement Review**: Pre-commit review screen with duplicate detection and boundary checks.

---

## ⚡ Backend REST API (Python + FastAPI)

### Tech Stack
- **Framework**: FastAPI (Python 3.14 / 3.12 compatible)
- **Validation**: Pydantic v2 schemas
- **Database ORM**: SQLAlchemy 2.0 with PostgreSQL (Production) / SQLite (Development)
- **Security**: JWT tokens (15-min access, 7-day refresh), bcrypt password hashing, strict multi-tenant user data isolation
- **Automated Tests**: Pytest test suite covering decimal precision, caps, exclusions, duplicate rejection, and cross-user isolation.

### Running Backend Locally
```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated test suite
pytest tests/ -v

# 4. Start local development server
uvicorn app.main:app --reload --port 8000
```
Open API docs in browser: `http://localhost:8000/docs`

### Running with Docker Compose (PostgreSQL + API)
```bash
docker-compose up --build -d
```

---

## 🧪 Automated Test Verification

All financial calculations and security boundaries are backed by deterministic automated tests:
```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

### Verified Test Cases:
- `test_decimal_precision_exact_cents`: Verifies exact decimal precision without floating-point artifacts.
- `test_reward_maximum_cap_enforcement`: Asserts that category spend caps (e.g. ₹1,000 grocery cap on RBL Shoprite) are strictly enforced.
- `test_minimum_spend_hurdle_fallback`: Ensures transactions below minimum spend fall back to base rates.
- `test_fuel_category_exclusion`: Verifies excluded categories yield zero rewards without active surcharge waivers.
- `test_offer_expiry_date_handling`: Confirms expired promotions are ignored.
- `test_multiple_planned_payments_and_confirmed_reconciliation`: Validates multi-tranche payment calculations.
- `test_overpayment_and_credit_balance`: Validates boundary conditions when payments exceed balance.
- `test_auth_and_cross_user_isolation`: Proves that User B cannot access User A's financial assets.
- `test_seed_and_matcher_endpoint`: Verifies seed fixture population and Amazon shopping card recommendations.

---

## 📁 Repository Structure
```
├── android/                   # Android Jetpack Compose application
│   ├── app/
│   │   ├── src/main/java/com/cardwise/app/
│   │   │   ├── domain/model/  # Core domain entities
│   │   │   ├── domain/engine/ # Payment ledger & Matcher math engines
│   │   │   ├── data/local/    # Room Database, DAOs, Entities, SampleData
│   │   │   ├── data/repository/
│   │   │   ├── ui/theme/      # Material 3 Emerald/Slate Theme
│   │   │   ├── ui/components/ # MetricCard, MaskedCardItem, ExplainableCard
│   │   │   ├── ui/screens/    # Home, Wallet, Matcher, Payments, Rewards, etc.
│   │   │   └── worker/        # WorkManager PaymentReminderWorker
│   │   └── src/test/java/     # JUnit test suite
├── backend/                   # FastAPI backend server
│   ├── app/
│   │   ├── api/v1/            # Auth, Cards, Statements, Payments, Matcher, etc.
│   │   ├── core/              # Config & Security
│   │   ├── db/                # SQLAlchemy session & Base
│   │   ├── models/            # SQLAlchemy declarative models
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   ├── services/          # Matching engine & Payment calculator
│   │   └── fixtures/          # 10 Synthetic card fixtures
│   ├── tests/                 # Pytest automated test suite
│   └── requirements.txt
├── docs/                      # Comprehensive engineering documentation
│   ├── ARCHITECTURE.md
│   ├── REQUIREMENTS.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_SPECIFICATION.md
│   ├── SECURITY_AND_PRIVACY.md
│   ├── TEST_PLAN.md
│   ├── ANDROID_RELEASE_GUIDE.md
│   ├── KNOWN_LIMITATIONS.md
│   ├── DECISIONS.md
│   └── PROGRESS.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```
