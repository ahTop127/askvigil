import uuid
from tortoise import fields
from tortoise.models import Model


class UserSession(Model):
    # Use UUID as the primary key and set the default value to automatically generate uuid4
    session_id = fields.UUIDField(pk=True, default=uuid.uuid4)
    # Assign values only at the time of creation
    created_at = fields.DatetimeField(auto_now_add=True)
    # The time will be automatically refreshed each time.save() is called to update the record
    last_active_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_sessions"

    def __str__(self):
        return str(self.session_id)
