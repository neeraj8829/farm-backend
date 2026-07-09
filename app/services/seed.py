import logging

from app.core.config import settings
from app.core.database import db
from app.core.security import hash_password, verify_password
from app.utils.datetime import date_offset, new_id, now_utc


log = logging.getLogger("serenity")


async def seed_database() -> None:
    await seed_admin()
    await seed_property()
    await seed_media()
    await seed_reviews()
    await seed_pricing_rules()
    await seed_blocked_dates()
    await seed_bookings()
    await seed_airbnb_sync()
    await create_indexes()


async def seed_admin() -> None:
    existing = await db.users.find_one({"email": settings.admin_email})
    if not existing:
        await db.users.insert_one({
            "id": new_id(),
            "email": settings.admin_email,
            "password_hash": hash_password(settings.admin_password),
            "name": "Owner",
            "role": "admin",
            "created_at": now_utc().isoformat(),
        })
        log.info("Seeded admin: %s", settings.admin_email)
        return

    if not verify_password(settings.admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": settings.admin_email},
            {"$set": {"password_hash": hash_password(settings.admin_password)}},
        )
        log.info("Updated admin password from .env")


async def seed_property() -> None:
    if await db.property.find_one({"id": "prop-1"}):
        return

    await db.property.insert_one({
        "id": "prop-1",
        "name": "Serenity Farmhouse",
        "tagline": "A private retreat wrapped in orchards, birdsong and open skies.",
        "location": "Lonavala, Maharashtra",
        "address": "Village Bhamburde, Off Old Mumbai-Pune Highway, Lonavala 410401",
        "description": (
            "Set across two acres of mango and guava orchards, Serenity Farmhouse is "
            "a slow-living hideaway for families and small groups. Wake to the smell "
            "of filter coffee on the verandah, spend afternoons by the private pool, "
            "and end the day around a crackling bonfire under a canopy of stars."
        ),
        "maxGuests": 14,
        "bedrooms": 4,
        "bathrooms": 4,
        "basePricePerNight": 18500,
        "cleaningFee": 2500,
        "taxRatePct": 12,
        "checkIn": "2:00 PM",
        "checkOut": "11:00 AM",
        "houseRules": [
            "No loud music after 10 PM (village noise policy).",
            "Pets welcome with prior notice.",
            "No smoking indoors.",
            "Fireworks and DJ parties not permitted.",
            "Additional guests beyond max capacity must be pre-approved.",
        ],
        "amenities": [
            {"icon": "waves", "label": "Private Pool"},
            {"icon": "trees", "label": "2 acre Orchard"},
            {"icon": "flame", "label": "Outdoor Bonfire"},
            {"icon": "chef-hat", "label": "Chef on Request"},
            {"icon": "car", "label": "Parking (6 cars)"},
            {"icon": "wifi", "label": "High-speed Wi-Fi"},
            {"icon": "tv", "label": "Smart TV & Projector"},
            {"icon": "wind", "label": "AC in all Rooms"},
            {"icon": "utensils", "label": "Fully-stocked Kitchen"},
            {"icon": "paw-print", "label": "Pet Friendly"},
            {"icon": "gamepad-2", "label": "Board Games & Carrom"},
            {"icon": "sun", "label": "Sun Loungers"},
        ],
        "faqs": [
            {
                "q": "Are pets allowed?",
                "a": "Yes, small and medium sized pets are welcome. Please inform us in advance so we can prepare the property.",
            },
            {
                "q": "Can we host a private party or event?",
                "a": "Small family gatherings (birthdays, anniversaries) are welcome. Loud DJ parties, weddings and events with external caterers are not permitted.",
            },
            {
                "q": "Is there someone at the property?",
                "a": "A caretaker lives on-site and is available for assistance, but respects your privacy. A cook can be arranged on request (Rs.800/day).",
            },
            {
                "q": "What is the cancellation policy?",
                "a": "Full refund up to 14 days before check-in. 50% refund up to 7 days before check-in. Non-refundable within 7 days.",
            },
            {
                "q": "How do we reach the property?",
                "a": "The farmhouse is 90 minutes from Mumbai and 2 hours from Pune. Detailed directions are shared post-booking.",
            },
            {
                "q": "Is there a minimum stay?",
                "a": "Yes, a 2-night minimum on weekends and long weekends. Weekday stays are flexible.",
            },
        ],
    })
    log.info("Seeded property")


async def seed_media() -> None:
    if await db.media.count_documents({}) != 0:
        return

    media_seed = [
        ("Exterior", "https://images.pexels.com/photos/5768733/pexels-photo-5768733.jpeg", True, "Serenity Farmhouse exterior at golden hour"),
        ("Pool", "https://images.unsplash.com/photo-1658211342697-58df7f68ed0c?auto=format&fit=crop&w=1600&q=80", False, "Private pool with sun loungers"),
        ("Rooms", "https://images.pexels.com/photos/30767894/pexels-photo-30767894.jpeg", False, "Rustic bedroom with wood accents"),
        ("Bonfire", "https://images.pexels.com/photos/7263354/pexels-photo-7263354.jpeg", False, "Guests around evening bonfire"),
        ("Lawn", "https://images.unsplash.com/photo-1499696010180-025ef6e1a8f9?auto=format&fit=crop&w=1600&q=80", False, "Open lawn with seating"),
        ("Kitchen", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80", False, "Fully stocked kitchen"),
        ("Exterior", "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1600&q=80", False, "Verandah at dusk"),
        ("Rooms", "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1600&q=80", False, "Master suite"),
        ("Pool", "https://images.unsplash.com/photo-1519974719765-e6559eac2575?auto=format&fit=crop&w=1600&q=80", False, "Poolside evening"),
        ("Lawn", "https://images.unsplash.com/photo-1464146072230-91cabc968266?auto=format&fit=crop&w=1600&q=80", False, "Orchard walk"),
        ("Bonfire", "https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?auto=format&fit=crop&w=1600&q=80", False, "Night view with fire pit"),
        ("Kitchen", "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=1600&q=80", False, "Dining area"),
    ]
    docs = []
    for i, (category, url, is_hero, alt) in enumerate(media_seed):
        docs.append({
            "id": new_id(),
            "type": "image",
            "category": category,
            "url": url,
            "alt": alt,
            "isHero": is_hero,
            "sortOrder": i,
            "created_at": now_utc().isoformat(),
        })

    await db.media.insert_many(docs)
    log.info("Seeded media (%d items)", len(docs))


async def seed_reviews() -> None:
    if await db.reviews.count_documents({}) != 0:
        return

    await db.reviews.insert_many([
        {
            "id": new_id(),
            "name": "Ananya & family",
            "location": "Mumbai",
            "rating": 5,
            "quote": "The pool at sunset, warm ghar-ka-khana, and the friendliest caretaker. We didn't want to leave. Already planning our next stay.",
        },
        {
            "id": new_id(),
            "name": "Kabir S.",
            "location": "Pune",
            "rating": 5,
            "quote": "Booked for a birthday weekend with 12 friends. The bonfire and open lawn made for the most memorable night. Genuinely felt like a boutique villa.",
        },
        {
            "id": new_id(),
            "name": "Ritu Malhotra",
            "location": "Bengaluru",
            "rating": 5,
            "quote": "Clean, private, thoughtfully done up. The mango orchard is a dream - we plucked our own for breakfast. Highest recommendation.",
        },
    ])
    log.info("Seeded reviews")


async def seed_pricing_rules() -> None:
    if await db.pricing_rules.count_documents({}) != 0:
        return

    await db.pricing_rules.insert_many([
        {"id": new_id(), "label": "Weekend surcharge", "startDate": date_offset(4), "endDate": date_offset(5), "pricePerNight": 24500},
        {"id": new_id(), "label": "Festival week", "startDate": date_offset(20), "endDate": date_offset(25), "pricePerNight": 29500},
        {"id": new_id(), "label": "Long weekend", "startDate": date_offset(11), "endDate": date_offset(13), "pricePerNight": 26500},
    ])
    log.info("Seeded pricing rules")


async def seed_blocked_dates() -> None:
    if await db.blocked_dates.count_documents({}) != 0:
        return

    await db.blocked_dates.insert_many([
        {"id": new_id(), "date": date_offset(7), "source": "direct"},
        {"id": new_id(), "date": date_offset(8), "source": "direct"},
        {"id": new_id(), "date": date_offset(9), "source": "direct"},
        {"id": new_id(), "date": date_offset(15), "source": "airbnb"},
        {"id": new_id(), "date": date_offset(16), "source": "airbnb"},
        {"id": new_id(), "date": date_offset(17), "source": "airbnb"},
        {"id": new_id(), "date": date_offset(28), "source": "direct"},
    ])
    log.info("Seeded blocked dates")


async def seed_bookings() -> None:
    if await db.bookings.count_documents({}) != 0:
        return

    await db.bookings.insert_many([
        {"id": "BK-2041", "guestName": "Aarav Mehta", "guestEmail": "aarav@example.com", "guestPhone": "+91 98200 12345", "checkIn": date_offset(7), "checkOut": date_offset(10), "guests": 8, "totalAmount": 74500, "paymentMode": "online", "paymentStatus": "paid", "bookingStatus": "confirmed", "source": "direct", "createdAt": now_utc().isoformat()},
        {"id": "BK-2042", "guestName": "Priya Nair", "guestEmail": "priya@example.com", "guestPhone": "+91 90040 55521", "checkIn": date_offset(15), "checkOut": date_offset(18), "guests": 6, "totalAmount": 68000, "paymentMode": "airbnb", "paymentStatus": "paid", "bookingStatus": "confirmed", "source": "airbnb", "createdAt": now_utc().isoformat()},
        {"id": "BK-2043", "guestName": "Rohan Kapoor", "guestEmail": "rohan.k@example.com", "guestPhone": "+91 99870 34112", "checkIn": date_offset(11), "checkOut": date_offset(13), "guests": 4, "totalAmount": 55500, "paymentMode": "offline", "paymentStatus": "pending", "bookingStatus": "pending", "source": "direct", "createdAt": now_utc().isoformat()},
        {"id": "BK-2044", "guestName": "Sneha Reddy", "guestEmail": "sneha.r@example.com", "guestPhone": "+91 98450 78632", "checkIn": date_offset(28), "checkOut": date_offset(30), "guests": 10, "totalAmount": 82000, "paymentMode": "online", "paymentStatus": "paid", "bookingStatus": "confirmed", "source": "direct", "createdAt": now_utc().isoformat()},
        {"id": "BK-2038", "guestName": "Vikram Shah", "guestEmail": "vikram@example.com", "guestPhone": "+91 98100 22200", "checkIn": date_offset(-3), "checkOut": date_offset(-1), "guests": 6, "totalAmount": 54000, "paymentMode": "online", "paymentStatus": "paid", "bookingStatus": "completed", "source": "direct", "createdAt": now_utc().isoformat()},
    ])
    log.info("Seeded bookings")


async def seed_airbnb_sync() -> None:
    if await db.airbnb_sync.find_one({"id": "sync-1"}):
        return

    await db.airbnb_sync.insert_one({
        "id": "sync-1",
        "importUrl": "https://www.airbnb.co.in/calendar/ical/12345.ics?s=abc123",
        "exportUrl": "https://serenityfarm.example.com/api/ical/export.ics",
        "lastSyncedAt": now_utc().isoformat(),
        "syncFrequencyHours": 2,
    })
    log.info("Seeded airbnb sync")


async def create_indexes() -> None:
    await db.users.create_index("email", unique=True)
    await db.media.create_index("sortOrder")
    await db.bookings.create_index("checkIn")
    await db.bookings.create_index("id", unique=True)
    await db.blocked_dates.create_index("date", unique=True)

