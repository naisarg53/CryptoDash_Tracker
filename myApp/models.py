from django.db import models
import requests

class PurchaseHistory(models.Model):
    username = models.CharField(max_length=200)
    coin_name = models.CharField(max_length=200)
    sub_Total = models.DecimalField(max_digits=10, decimal_places=2)
    quantity= models.PositiveIntegerField(default=0, null=True)
    coin_id = models.CharField(max_length=50,default="na")

    def __str__(self):
        return self.coin_name
class CoinsDetails(models.Model):
    def __str__(self):
        s=self.name+" "+self.symbol
        return s

    id=models.CharField(primary_key=True,max_length=50)
    symbol=models.CharField(max_length=50)
    name=models.CharField(max_length=200)
    image=models.URLField()



