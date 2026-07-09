from fastapi import APIRouter

from app.api.routes import (
    airbnb_sync,
    auth,
    blocked_dates,
    bookings,
    health,
    ical,
    media,
    pricing_rules,
    property,
    reviews,
)


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(property.router)
api_router.include_router(reviews.router)
api_router.include_router(media.router)
api_router.include_router(pricing_rules.router)
api_router.include_router(blocked_dates.router)
api_router.include_router(bookings.router)
api_router.include_router(airbnb_sync.router)
api_router.include_router(ical.router)
api_router.include_router(health.router)

