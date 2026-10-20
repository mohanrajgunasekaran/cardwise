# CardWise Known Limitations & Mitigations

## 1. Architectural & Domain Boundaries

### 1.1 Non-Custodial Manual Payment Reconciliation
- **Limitation**: CardWise does not connect to bank accounts or payment gateways (UPI/IMPS/NEFT) to automatically verify whether a scheduled payment was actually received by the issuing bank.
- **Mitigation**: Clear status workflow: Payments start as `PLANNED`, progress to `SUBMITTED`, and only become `CONFIRMED` when explicitly confirmed by the user.

### 1.2 Dynamic Bank Reward Rule Changes
- **Limitation**: Banks in India frequently devalue credit card reward rates, add exclusion categories (e.g., utility bill caps, rent payment surcharges), and alter minimum spend slabs without prior standard notifications.
- **Mitigation**: Offers and rules contain `valid_to` timestamps and a confidence rating (`VERIFIED`, `ESTIMATED`, `COMMUNITY`). When a rule is unverified or expired, the UI highlights this with a badge and asks the user to confirm.

### 1.3 Statement Parser OCR Variance
- **Limitation**: Bank statement PDF formats vary widely between issuers and over time. Protected PDFs require user password entry locally.
- **Mitigation**: Statement extraction always routes through a pre-save Review screen with individual confidence scores per field. The user has full control to edit any field before it is committed to storage.

### 1.4 Background Notification Delivery
- **Limitation**: Aggressive OEM battery-optimization regimes (e.g., Xiaomi MIUI/HyperOS, OnePlus OxygenOS, Samsung OneUI) may defer or kill WorkManager periodic background tasks.
- **Mitigation**: Guide the user via an in-app prompt to disable battery optimization for CardWise to ensure critical due date reminders fire reliably.
