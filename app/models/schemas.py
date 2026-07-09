from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PropertyUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    tagline: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    maxGuests: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    basePricePerNight: Optional[float] = None
    cleaningFee: Optional[float] = None
    taxRatePct: Optional[float] = None
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    houseRules: Optional[list[str]] = None
    amenities: Optional[list[dict]] = None
    faqs: Optional[list[dict]] = None


class MediaCreate(BaseModel):
    type: Literal["image", "video"] = "image"
    category: str
    url: str
    alt: str = ""
    isHero: bool = False


class PricingRuleCreate(BaseModel):
    startDate: str
    endDate: str
    pricePerNight: float
    label: str


class BlockedDateToggle(BaseModel):
    date: str


class BookingCreate(BaseModel):
    guestName: str
    guestEmail: EmailStr
    guestPhone: str
    checkIn: str
    checkOut: str
    guests: int
    totalAmount: float
    paymentMode: Literal["online", "offline"]
    specialRequests: Optional[str] = ""


class BookingStatusUpdate(BaseModel):
    bookingStatus: Literal["confirmed", "pending", "cancelled", "completed"]


class AirbnbSyncUpdate(BaseModel):
    importUrl: Optional[str] = None
    syncFrequencyHours: Optional[int] = None
