from django.db import models
from django.conf import settings
# Create your models here.


class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.email})"


class UserSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    competitors = models.JSONField(default=list)
    linkedin = models.JSONField(default=list)
    references = models.JSONField(default=list)
    youtube = models.JSONField(default=list)

    def __str__(self):
        return f"Sources for {self.user.email}"