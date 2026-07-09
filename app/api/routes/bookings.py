from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import BookingCreate, BookingStatusUpdate
from app.utils.datetime import iter_date_range, make_booking_id, new_id, now_utc


router = APIRouter(tags=["bookings"])


@router.get("/bookings")
async def list_bookings(user: dict = Depends(require_admin)):
    return await db.bookings.find({}, {"_id": 0}).sort("checkIn", 1).to_list(1000)


@router.post("/bookings")
async def create_booking(body: BookingCreate):
    if body.checkOut <= body.checkIn:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")

    prop = await db.property.find_one({"id": "prop-1"})
    if prop and body.guests > prop.get("maxGuests", 999):
        raise HTTPException(status_code=400, detail=f"Max {prop['maxGuests']} guests allowed")

    nights = list(iter_date_range(body.checkIn, body.checkOut))
    for ymd in nights:
        if await db.blocked_dates.find_one({"date": ymd}):
            raise HTTPException(status_code=409, detail=f"Dates unavailable ({ymd})")
        overlap = await db.bookings.find_one({
            "bookingStatus": {"$in": ["confirmed", "pending"]},
            "checkIn": {"$lte": ymd},
            "checkOut": {"$gt": ymd},
        })
        if overlap:
            raise HTTPException(status_code=409, detail=f"Dates unavailable ({ymd})")

    doc = {
        "id": make_booking_id(),
        "guestName": body.guestName,
        "guestEmail": body.guestEmail,
        "guestPhone": body.guestPhone,
        "checkIn": body.checkIn,
        "checkOut": body.checkOut,
        "guests": body.guests,
        "totalAmount": body.totalAmount,
        "paymentMode": body.paymentMode,
        "paymentStatus": "paid" if body.paymentMode == "online" else "pending",
        "bookingStatus": "confirmed" if body.paymentMode == "online" else "pending",
        "source": "direct",
        "specialRequests": body.specialRequests or "",
        "createdAt": now_utc().isoformat(),
    }
    await db.bookings.insert_one(doc)
    doc.pop("_id", None)

    if doc["bookingStatus"] == "confirmed":
        for ymd in nights:
            if not await db.blocked_dates.find_one({"date": ymd}):
                await db.blocked_dates.insert_one(
                    {"id": new_id(), "date": ymd, "source": "direct"}
                )

    return doc


@router.patch("/bookings/{bid}/status")
async def update_booking_status(
    bid: str,
    body: BookingStatusUpdate,
    user: dict = Depends(require_admin),
):
    booking = await db.bookings.find_one({"id": bid})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await db.bookings.update_one(
        {"id": bid},
        {"$set": {"bookingStatus": body.bookingStatus}},
    )

    for ymd in iter_date_range(booking["checkIn"], booking["checkOut"]):
        if body.bookingStatus == "confirmed":
            if not await db.blocked_dates.find_one({"date": ymd}):
                await db.blocked_dates.insert_one(
                    {"id": new_id(), "date": ymd, "source": "direct"}
                )
        elif body.bookingStatus == "cancelled":
            await db.blocked_dates.delete_one({"date": ymd, "source": "direct"})

    return await db.bookings.find_one({"id": bid}, {"_id": 0})

