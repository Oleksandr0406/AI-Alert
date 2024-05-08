from django.db import models

# Create your models here.


class Location(models.Model):
    city = models.CharField(max_length=85, null=False)
    state = models.CharField(max_length=85, null=False)
    county = models.CharField(max_length=85, null=False)

    def __str__(self):
        return f"{self.city}, {self.state}, {self.county}"


class FeedAudio(models.Model):
    pass


class Feed(models.Model):
    type = models.CharField(max_length=100)
    external_id = models.PositiveIntegerField()
    location_id = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True)
    audio = models.ForeignKey(FeedAudio, on_delete=models.PROTECT, null=True, blank=True)
