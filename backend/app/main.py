from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
from app.api.v1 import auth, cards, statements, payments, matcher, offers, dashboard, documents

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CardWise Credit Card Benefits & Payment Manager REST API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(cards.router, prefix=f"{settings.API_V1_STR}/cards", tags=["Credit Cards"])
app.include_router(statements.router, prefix=f"{settings.API_V1_STR}/statements", tags=["Statements"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["Payments"])
app.include_router(matcher.router, prefix=f"{settings.API_V1_STR}/matcher", tags=["Smart Card Matcher"])
app.include_router(offers.router, prefix=f"{settings.API_V1_STR}/offers", tags=["Offers & Rewards"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Official Documents"])

# Mount static web client assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "CardWise Backend API", "version": settings.VERSION}

