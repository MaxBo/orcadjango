from django.db import models

import orca

@orca.injectable
def inj1():
    return 'INJ 1'

@orca.injectable
def inj2():
    return 'INJ 2'

# Create your models here.

class Injectables(models.Model):
    name = models.TextField()
    value = models.TextField()

