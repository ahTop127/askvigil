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
