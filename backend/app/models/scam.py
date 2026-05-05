from tortoise import fields, models
from enum import Enum


# Define an enumeration class that perfectly corresponds to the CHECK constraint in DDL
class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    URL = "url"
    QR = "qr"


class ScamCategory(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)

    class Meta:
        table = "scam_categories"


class DetectionLog(models.Model):
    id = fields.IntField(pk=True)
    # Tortoise will automatically generate the session_id column in the database
    session = fields.ForeignKeyField(
        "models.UserSession",
        related_name="detections",
        null=True,
        on_delete=fields.SET_NULL,
    )
    # Use CharEnumField to directly map the verification rules
    input_type = fields.CharEnumField(InputType, max_length=20)
    input_content = fields.TextField()
    risk_score = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "detection_logs"


class GuidanceStep(models.Model):
    id = fields.IntField(pk=True)
    # Youdaoplaceholder0 column
    category = fields.ForeignKeyField(
        "models.ScamCategory", related_name="steps", on_delete=fields.CASCADE
    )
    step_number = fields.IntField()
    action_text = fields.TextField()

    class Meta:
        table = "guidance_steps"
        # error_ddl: UNIQUE（category_id, step_number）
        unique_together = (("category", "step_number"),)
