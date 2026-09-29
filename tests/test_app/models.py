from django.db import models


class Dummy(models.Model):
    field_1 = models.IntegerField(default=1)
    field_2 = models.IntegerField(default=2)
    field_3 = models.IntegerField(default=3)
