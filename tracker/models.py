from django.db import models
from django.utils import timezone
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    null=True,  # <== allow NULL for old data
    blank=True, # <== allow blank in forms/admin
) 
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"

class Budget(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, unique=False)
    limit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.category} - Limit: {self.limit}"