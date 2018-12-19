from django.db import models


# Create your models here.

class Injectables(models.Model):
    name = models.TextField()
    value = models.TextField()

