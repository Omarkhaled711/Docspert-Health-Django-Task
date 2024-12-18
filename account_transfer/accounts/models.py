from django.db import models
from decimal import Decimal
import uuid

# Create your models here.


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=10, decimal_places=3)

    def deposit(self, amount):
        self.balance += Decimal(amount)
        self.save()

    def withdraw(self, amount):
        if self.balance >= Decimal(amount):
            self.balance -= Decimal(amount)
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.name} has {self.balance}$"
