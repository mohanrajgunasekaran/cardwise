# CardWise Project Plan

## Project Overview
CardWise is a production-oriented personal credit card benefits optimizer and bill payment manager designed for Indian credit card users. It bridges the gap between complex reward programs, statement cycles, and payment planning while preserving strict privacy (no banking credentials, OTPs, CVVs, or full card numbers).

---

## Phase Breakdown & Traceable Roadmap

### Phase 1: Architecture, Requirements & Workspace Setup [COMPLETED]
- [x] Inspect workspace and local tooling (Python 3.14, Android SDK 36.1, JBR 25).
- [x] Establish Git repository and strict `.gitignore`.
- [x] Create Architecture Decision Records (`docs/DECISIONS.md`).
- [x] Document System Requirements Specification (`docs/REQUIREMENTS.md`).
- [x] Create Complete Database Schema & Entity Relationships (`docs/DATABASE_SCHEMA.md`).
- [x] Produce REST API Specification with OpenAPI contracts (`docs/API_SPECIFICATION.md`).
- [x] Detail Security & Privacy Blueprint (`docs/SECURITY_AND_PRIVACY.md`).
- [x] Document Multi-tier Automated Test Plan (`docs/TEST_PLAN.md`).
- [x] Detail Android Release, Keystore & Play Store Guide (`docs/ANDROID_RELEASE_GUIDE.md`).
- [x] Enumerate Known Limitations & Mitigations (`docs/KNOWN_LIMITATIONS.md`).
- [x] Initialize Progress Tracker (`docs/PROGRESS.md`).

### Phase 2: Repository Structure & Core Engine Setup [IN PROGRESS]
- [ ] Establish directory structures (`/android`, `/backend`, `/docs`, `/fixtures`).
- [ ] Configure Backend environment (FastAPI, SQLAlchemy, Alembic, Pydantic v2, Pytest).
- [ ] Configure Android Gradle environment (Jetpack Compose, Material 3, Navigation, Room, Coroutines, WorkManager).
- [ ] Implement deterministic synthetic fixtures for the 10 reference cards.
- [ ] Establish Docker Compose configuration for PostgreSQL and local API dev.

### Phase 3: UI Design System, Core Navigation & User Context
- [ ] Create Material 3 color system (accessible emerald/teal accent, slate neutral, dark/light modes, zero prohibited violet/purple).
- [ ] Implement top-level Navigation Graph:
  1. Home (Dashboard)
  2. My Cards (Wallet)
  3. Card Matcher (Smart Recommendation Engine)
  4. Payments (Statement Balances & Payment Plans)
  5. Rewards (Offers, Points, Cashback & Expiring Benefits)
  6. Settings (Security, Preferences, Data Export/Erase)
- [ ] Build reusable UI components (MetricCards, MaskedCardBadge, DueDateTag, CurrencyText, CalculationBreakdownCard).

### Phase 4: Card Wallet, Database Persistence & Payment Planner
- [ ] Local Room Database with SQLite & Keystore-backed encryption for sensitive tokens.
- [ ] Normalized Backend database models and Alembic migrations.
- [ ] CRUD operations for Cards, Statements, and Payments with strict user-isolation.
- [ ] Decimal-safe financial calculation engine for payment planner:
  - Remaining Amount = Statement Balance - Confirmed Payments - Planned Payments.
  - Multi-part payment planning against statement balances.
  - Due date warning & interest prevention reminders.

### Phase 5: Smart Card Matcher & Explainable Reward Calculation Engine
- [ ] Purchase categories (Shopping, Travel, Flights, Hotels, Utilities, Groceries, Fuel, Insurance, Dining, etc.).
- [ ] Rules evaluation: base earn rate, category multipliers, merchant whitelist/blacklist, spend caps, minimum spend, expiry date.
- [ ] Transparent net benefit formula in INR (Cashback + Discounts + Points Monetary Value - Additional Fees).
- [ ] Explainable breakdown cards with step-by-step logic and verification confidence rating.

### Phase 6: Statement Import, Local Notifications & Offline Sync
- [ ] Statement review and import screen with duplicate detection and field confidence.
- [ ] Android WorkManager periodic worker for upcoming due dates & expiring offers.
- [ ] Local Android notification channels with notification permission handling.
- [ ] Offline caching and graceful network recovery.

### Phase 7: Automated Testing, Security Audit & Code Verification
- [ ] Unit & Property tests for financial calculation engine (Pytest + JUnit).
- [ ] API integration tests verifying cross-user security barrier.
- [ ] Room DAO and database migration validation tests.
- [ ] ViewModel state verification and Compose UI component checks.

### Phase 8: Signed Release & Production Documentation
- [ ] Gradle release build script configuration with ProGuard/R8 rules.
- [ ] Keystore generation guide and App Bundle (AAB) packaging steps.
- [ ] Comprehensive README.md with developer setup steps.
