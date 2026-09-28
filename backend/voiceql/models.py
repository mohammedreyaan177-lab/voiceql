from django.db import models

class sales(models.Model):
    id = models.AutoField(primary_key=True)
    products = models.CharField(max_length=200)
    price = models.FloatField()
