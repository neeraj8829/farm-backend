import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_title: str = "Serenity Farmhouse API"
    mongo_url: str = os.environ["MONGO_URL"]
    db_name: str = os.environ["DB_NAME"]
    jwt_secret: str = os.environ["JWT_SECRET"]
    jwt_algo: str = "HS256"
    jwt_hours: int = 24
    admin_email: str = os.environ.get("ADMIN_EMAIL", "admin@serenityfarm.com")
    admin_password: str = os.environ.get("ADMIN_PASSWORD", "admin123")
    cors_origins: tuple[str, ...] = tuple(
        os.environ.get("CORS_ORIGINS", "*").split(",")
    )
    cloudinary_cloud_name: str = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key: str = os.environ.get("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.environ.get("CLOUDINARY_API_SECRET", "")
    cloudinary_folder: str = (
        os.environ.get("CLOUDINARY_FOLDER", "farmhouse") or "farmhouse"
    )


settings = Settings()