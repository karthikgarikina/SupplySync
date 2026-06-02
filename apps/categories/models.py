from django.db import models

from core.models import BaseModel


class Category(BaseModel):
    category_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    parent_category = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    class Meta:
        db_table = "categories"

    def __str__(self):
        return f"{self.category_code} - {self.name}"

