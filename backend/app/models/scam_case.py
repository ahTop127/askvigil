from enum import Enum

from tortoise import fields
from tortoise.models import Model


class ScamTypeEnum(str, Enum):
    JOB_SCAM = "JOB_SCAM"
    PHISHING = "phishing"
    QR_CODE_SCAM = "qr_code_scam"
    OTP_SCAM = "otp_scam"
    SUSPICIOUS_LINK = "suspicious_link"


class PlatformEnum(str, Enum):
    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    PHONE_CALL = "phone_call"
    PHONE_MESSAGE = "phone_message"
    EMAIL = "email"
    OTHER = "other"


class ScamCase(Model):
    id = fields.IntField(pk=True)

    # basic content
    title = fields.CharField(max_length=255, description="Case Title")
    content = fields.TextField(description="Complete description of the case")
    source = fields.CharField(
        max_length=512,
        null=True,
        description="Source information (such as Bernama, The Star)",
    )
    url_link = fields.CharField(
        max_length=512, null=True, description="Link to the case"
    )

    # Filtering and classification dimensions (add index=True to improve query performance)
    scam_type = fields.CharEnumField(
        ScamTypeEnum, index=True, description="Types of fraud"
    )
    # field column, add index can search quickly
    platform = fields.CharEnumField(
        PlatformEnum,
        index=True,
        description="The platforms where the incident occurred (such as TikTok, WhatsApp",
    )
    news_date = fields.DateField(index=True, description="News/Date of the incident")

    class Meta:
        table = "scam_cases"
        # desc
        ordering = ["-news_date"]

    def __str__(self):
        return f"[{self.scam_type.value}] {self.title}"
