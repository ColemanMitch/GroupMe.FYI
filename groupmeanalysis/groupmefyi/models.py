from django.db import models
#from django.contrib.postgres.fields import JSONField


# Create your models here.
""" class Groups(models.Model): 
    attachments = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.SlugField(blank=True, null=True)
    created_at = models.IntegerField(default=0)
    favorited_by = models.CharField(blank=True, null=True)
    group_id = models.CharField(max_length=15, blank=True, null=True)
    id = models.IntegerField(default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    sender_id = models.IntegerField(default=0)
    sender_type = models.CharField(max_length=25, blank=True, null=True)
    source_guid = models.CharField(max_length=255, blank=True, null=True)
    system = models.BooleanField(max_length=255, blank=True, null=True)
    text = models.CharField(blank=True, null=True)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=5, blank=True, null=True)
    event = models.CharField(blank=True, null=True)

    objects = GroupManager()

    class Meta:
        verbose_name_plural = "groups"

    def __str__(self):
        return self.name
 """