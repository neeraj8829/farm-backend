from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.database import db


router = APIRouter(tags=["ical"])


@router.get("/ical/export.ics")
async def export_ical():
    bookings = await db.bookings.find(
        {"bookingStatus": {"$in": ["confirmed", "pending"]}},
        {"_id": 0},
    ).to_list(1000)

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//SerenityFarmhouse//EN"]
    for b in bookings:
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{b['id']}@serenityfarm",
            f"DTSTART;VALUE=DATE:{b['checkIn'].replace('-', '')}",
            f"DTEND;VALUE=DATE:{b['checkOut'].replace('-', '')}",
            f"SUMMARY:Reserved - {b['id']}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return PlainTextResponse("\r\n".join(lines), media_type="text/calendar")

