# CardWise Architecture Decision Records (ADR)

## ADR-001: Mobile Architecture - Jetpack Compose & MVVM
- **Context**: Need a responsive, testable, modern Android interface adhering to Google's current architectural recommendations.
- **Decision**: Adopt 100% Jetpack Compose with Material 3, Navigation Compose, and Kotlin Coroutines/Flow in an MVVM pattern.
- **Consequences**: Declarative UI state reduces synchronization bugs; zero XML view overhead; seamless dynamic theming and accessible contrast.

## ADR-002: Monetary Calculations - Strict Decimal Arithmetics
- **Context**: Floating-point arithmetic (`Double`/`Float`) introduces rounding errors (e.g. `1999.99 * 0.05` accumulating fractional paise discrepancies).
- **Decision**: All financial fields must use `BigDecimal` on Android and Python's `Decimal` with explicit rounding modes (`ROUND_HALF_UP`) on the backend.
- **Consequences**: Absolute monetary accuracy; completely deterministic tests across languages.

## ADR-003: Backend Framework - Python with FastAPI & SQLAlchemy 2.0
- **Context**: High developer productivity, type safety via Pydantic v2, async performance, and rapid testing turnaround.
- **Decision**: Implement FastAPI with SQLAlchemy 2.0 ORM and Alembic migrations.
- **Consequences**: Automatic OpenAPI schema generation; clean separation of data models and Pydantic validation schemas.

## ADR-004: Zero Custodial Financial Credentials
- **Context**: Risk of storing full PANs, CVVs, or bank credentials.
- **Decision**: Store only masked identifiers (`XXXX-XXXX-XXXX-1234`). Never ask for passwords, PINs, or OTPs.
- **Consequences**: Significantly lowers security attack surface; keeps CardWise purely in the informational realm and compliant with privacy guidelines.

## ADR-005: Offline-First Local Data Storage
- **Context**: Users need immediate access to card limits, due dates, and reward calculations even with intermittent mobile network connectivity.
- **Decision**: Room SQLite database on Android acts as the single source of truth for UI state, synchronized via REST APIs to the backend.
- **Consequences**: High responsiveness; offline support out-of-the-box.
