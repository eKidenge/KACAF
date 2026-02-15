from django.db import models

class Partner(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="partners/logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
