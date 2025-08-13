import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ThemisGuard"

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "themisguard-scans")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "themisguard-reports")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # GCP Configuration
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    # GCP Credential Storage
    KMS_KEY_ALIAS: str = os.getenv(
        "KMS_KEY_ALIAS", "alias/compliantguard-gcp-credentials"
    )
    GCP_CREDENTIALS_TABLE: str = os.getenv(
        "GCP_CREDENTIALS_TABLE", "compliantguard-gcp-credentials"
    )

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_...")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

    class Config:
        env_file = ".env"


settings = Settings()
