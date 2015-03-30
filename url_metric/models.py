from django.db import models

class HostCounter(models.Model):
    hostname = models.CharField(max_length=100)
    count = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

