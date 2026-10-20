# CardWise Comprehensive Test Plan

## 1. Testing Strategy

The test suite enforces mathematical correctness, boundary condition stability, and zero cross-user access vulnerability.

```
       / \
      /   \     E2E / Integration Tests (API + DB)
     / ---- \
    /        \    Financial Engine Unit & Property Tests
   / -------- \
  /            \   Component & Model Unit Tests
```

---

## 2. Test Suites

### 2.1 Financial Calculation Engine Tests (Priority P0)
- **Decimal Precision**: No floating-point rounding errors (e.g., `0.1 + 0.2 == 0.30`).
- **Reward Caps**:
  - Verification that cashbacks exceeding the monthly limit are strictly capped (e.g., card capped at ₹1,000 does not award ₹1,200).
- **Minimum Spend Hurdles**:
  - Transactions below the minimum threshold (e.g., ₹500 min spend) receive base rate or zero, not promotional rate.
- **Excluded Categories**:
  - Verifying that fuel, rent, wallet loads, and government payments trigger exclusions where defined.
- **Remaining Plan Arithmetic**:
  - $\text{Remaining} = \text{Balance} - \text{Confirmed} - \text{Planned}$.
  - Boundary test: Negative remaining balances flagged for user confirmation.
- **Multiple Planned Payments**:
  - Summing 3+ planned disbursements against one statement.

### 2.2 Backend Security & Access Control Tests
- **Cross-User Leakage**: User A attempts to view, modify, or delete User B's cards, statements, or payments. Must return `404 Not Found` or `403 Forbidden`.
- **Token Tampering**: Expired, malformed, or unsigned JWT tokens rejected with `401 Unauthorized`.
- **Duplicate Statement Prevention**: Submitting duplicate statement for the same card and billing period returns `409 Conflict`.

### 2.3 Android Local Architecture Tests
- **Room Database DAOs**: Card insertion, updating limits, cascading statement deletion, archiving.
- **ViewModel State Machines**: Flow state changes through `Loading`, `Success`, `Empty`, and `Error` states.
- **WorkManager Notification Triggering**: Ensure reminder calculation correctly schedules notifications based on due dates.
