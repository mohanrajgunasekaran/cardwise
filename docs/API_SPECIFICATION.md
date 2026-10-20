# CardWise REST API Specification

## 1. Global Conventions

- **Base URL**: `/api/v1`
- **Content Type**: `application/json`
- **Authentication**: Bearer Token in `Authorization` header (`Bearer <access_token>`).
- **Error Response Format**:
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human readable explanation",
    "details": []
  }
}
```

---

## 2. Endpoints Summary

### Authentication (`/auth`)
- `POST /auth/register`: Register new user account.
- `POST /auth/login`: Authenticate and receive JWT access (15 min) and refresh tokens (7 days).
- `POST /auth/refresh`: Exchange refresh token for new access token.
- `GET /auth/me`: Retrieve current authenticated profile.

### Cards (`/cards`)
- `GET /cards`: List authenticated user's credit cards (with optional filtering by archived/active).
- `POST /cards`: Add a new card record (masked number, issuer, variant, limits, billing dates).
- `GET /cards/{card_id}`: Retrieve detailed card metadata and reward configuration.
- `PUT /cards/{card_id}`: Update card details (nickname, limits, cycle dates).
- `DELETE /cards/{card_id}`: Archive or delete card record.

### Statements (`/statements`)
- `GET /statements`: List statements, filterable by `card_id`, `is_paid`, or month.
- `POST /statements`: Record new monthly statement (checks for duplicate billing cycles).
- `GET /statements/{statement_id}`: Retrieve statement details with payment history & reconciliation.
- `PUT /statements/{statement_id}`: Update balance or payment status.

### Payments (`/payments`)
- `GET /payments`: List payments for a statement or across all user cards.
- `POST /payments`: Create a planned payment against an open statement.
- `POST /payments/{payment_id}/confirm`: Mark a planned payment as confirmed with execution timestamp.
- `DELETE /payments/{payment_id}`: Cancel a planned payment.

### Smart Card Matcher (`/matcher`)
- `POST /matcher/recommend`: Submit purchase details and receive sorted recommendation rankings with itemized calculation breakdowns.
  - **Request Body**:
    ```json
    {
      "purchase_amount": 4500.00,
      "category": "SHOPPING",
      "merchant": "Amazon",
      "transaction_date": "2026-10-20"
    }
    ```
  - **Response**:
    ```json
    {
      "best_card_id": "card-amazon-pay-icici",
      "recommendations": [
        {
          "card_id": "card-amazon-pay-icici",
          "card_name": "Amazon Pay ICICI Bank (ending 5541)",
          "estimated_net_benefit_inr": 225.00,
          "effective_rate_percent": 5.0,
          "benefit_breakdown": "5.0% Amazon Prime Accelerated Cashback on ₹4,500.00",
          "rule_applied": "Amazon Pay ICICI 5% Shopping Benefit",
          "is_verified": true,
          "notes": "Direct statement credit in next billing cycle"
        }
      ]
    }
    ```

### Offers & Rewards (`/offers`)
- `GET /offers`: Catalog of verified and community-reported bank offers.
- `GET /offers/expiring`: Offers expiring within the next 14 days.
