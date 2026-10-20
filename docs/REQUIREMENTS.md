# CardWise Requirements Specification (SRS)

## 1. Scope & Objective
CardWise is a personal finance management tool for Indian credit card holders to maximize reward accrual, prevent interest charges, and maintain visibility over statement cycles without compromising banking security.

### Core Philosophy
- **Zero Sensitive Credential Exposure**: Never ask for or store full 16-digit card numbers, CVVs, expiration dates, PINs, bank passwords, or OTPs.
- **Explainable Mathematics**: Reward calculations and payment schedules must be completely transparent with traceable mathematical steps.
- **Decimal Safety**: All monetary values must use high-precision decimals (`BigDecimal` in Kotlin / `Decimal` in Python). IEEE 754 floating-point calculations are strictly forbidden.

---

## 2. Functional Requirements (FR)

### FR-01: User Profile & Security Preferences
- Users register/authenticate with email & password or biometric device auth.
- Backend authenticates via short-lived JWT access tokens (15m) and sliding-window refresh tokens (7d).
- Local sensitive values (tokens, credentials) stored in encrypted shared preferences backed by Android Keystore.
- User data export (JSON/CSV) and irreversible account deletion ("Right to be Forgotten").

### FR-02: Credit Card Wallet Management
- Support multiple cards per user, including multiple variants from the same bank/issuer.
- Record fields:
  - `issuer`: Name of issuing bank (e.g., HDFC, ICICI, YES BANK, IndusInd, RBL, AU, IDFC).
  - `variant`: Product name (e.g., "Coral", "ACE", "Shoprite", "LIT").
  - `nickname`: Custom user label (e.g., "Primary Fuel Card").
  - `masked_number`: Last 4 digits only (e.g., "ending 7207").
  - `credit_limit` & `available_limit`: Optional Decimal amounts.
  - `billing_cycle_day`: Statement generation day (1-31).
  - `grace_period_days`: Days between statement date and due date (default: typically 15-20 days).
  - `annual_fee` & `joining_fee`: Decimal values with waiver conditions.
  - `status`: Active, Archived, or Closed.
  - `verification_status`: Verified vs Unverified/Estimated.

### FR-03: Statement Management
- Record monthly statements per card:
  - `statement_period_start` and `statement_period_end`
  - `statement_date`
  - `payment_due_date`
  - `total_balance` (Decimal)
  - `minimum_amount_due` (Decimal)
  - `is_paid`: Boolean indicator when cleared.
  - `source`: Manual entry or extracted document review.
- Prevent duplicate statement creation for identical billing cycles.
- Display a mandatory regulatory disclosure: *"Paying only the minimum amount due leads to interest accrual on the unpaid balance from the transaction date."*

### FR-04: Payment Planner
- Users can schedule incremental payments against open statements:
  - `planned_amount`: Monetary Decimal.
  - `planned_date`: Target payment date.
  - `status`: `PLANNED`, `SUBMITTED`, `CONFIRMED`, `CANCELLED`, `FAILED`.
  - `confirmed_date`: Timestamp when user marks transaction as confirmed with bank.
- Formula:
  $$\text{Remaining Unplanned Amount} = \text{Statement Balance} - \sum \text{Confirmed Payments} - \sum \text{Planned Payments}$$
- Do not let remaining balance go below zero without explicit user override (overpayment confirmation).

### FR-05: Smart Card Matcher Engine
- Input parameters:
  - `purchase_amount`: Monetary Decimal in INR.
  - `purchase_category`: Shopping, Travel, Flights, Hotels, Utilities, Subscriptions, Groceries, Fuel, Insurance, Dining, Other.
  - `merchant_name`: Optional string for merchant-specific offers (e.g., "Amazon", "Swiggy", "MakeMyTrip").
  - `transaction_date`: Default today.
- Evaluation rules:
  - Base reward rate (%) or points per ₹100 spent.
  - Category-specific accelerated multipliers.
  - Merchant-specific cashback/discounts.
  - Minimum spend thresholds (e.g., "Minimum ₹500 transaction").
  - Monthly or quarterly reward caps (e.g., "Max ₹1,000 cashback per month").
  - Excluded categories (e.g., Fuel surcharge exclusions, Rent, Government payments).
  - Redemption conversion rate (e.g., 1 reward point = ₹0.25).
  - Surcharges / convenience fees deduction.
- Output:
  - Ordered ranking of user's active cards by Net Value in ₹.
  - Itemized mathematical formula showing base, accelerated, caps, and deductions.

### FR-06: Rewards & Offer Tracker
- Aggregate reward points and cashback across cards.
- Track verified balances vs estimated balances.
- Expiring reward alerts (e.g., points expiring in < 30 days).

### FR-07: Local Notifications & Reminders
- Schedule local Android notifications via WorkManager:
  - T-5 days, T-2 days, and Due Date payment reminders.
  - Statement generation day reminder.
  - Offer expiration alerts.
- Check user-configured notification preferences (quiet hours, channels).

---

## 3. Non-Functional Requirements (NFR)

1. **Performance**:
   - Card Matcher calculation latency < 100ms for 20+ rules.
   - Android cold startup time < 1.5s on mid-tier devices.
2. **Offline-First Resilience**:
   - Complete local read/write access via Room SQLite cache.
   - Synchronizes seamlessly with backend when network is restored.
3. **Security & Privacy**:
   - TLS 1.3 enforced for API traffic.
   - Zero telemetry containing financial figures or account numbers.
   - OWASP Mobile Top 10 and API Security Top 10 compliance.
4. **Accessibility & Design**:
   - WCAG 2.1 AA contrast compliance across light and dark themes.
   - Minimum 48dp touch targets on interactive controls.
