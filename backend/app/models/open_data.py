from tortoise.models import Model
from tortoise import fields
from tortoise_vector.field import VectorField


class OpenDataSet(Model):
    id = fields.IntField(pk=True)
    source = fields.CharField(max_length=50)
    label = fields.CharField(max_length=20)
    original_text = fields.TextField()
    clean_text = fields.TextField()

    # Define a 384-dimensional vector field (null=True indicates that it is allowed to be empty)
    text_embedding = VectorField(vector_size=384, null=True)

    class Meta:
        table = "open_dataset"

class PhishingURL(Model):
    id = fields.IntField(pk=True)

    source = fields.CharField(max_length=50, description="dataset source")
    is_malicious = fields.BooleanField(default=True, description="True=Phishing website, False=Safe website")

    original_url = fields.TextField(description="The original URL might be a bit.ly short link")
    resolved_url = fields.TextField(null=True, description="Redirect the real long link after expansion")

    domain = fields.CharField(max_length=255, index=True, null=True, description="Clean the extracted core domain names, such as scam.com")
    path = fields.TextField(null=True, description="URL path, such as /login")

    preview_title = fields.CharField(max_length=500, null=True, description="The title of the captured web page (used for Link Preview)")

    url_embedding = VectorField(vector_size=768, null=True, description="The feature vector extracted by URLBERT (768-dim)")

    # Audit timestamp
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "phishing_url"
