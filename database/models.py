from django.db import models
from django.conf import settings
# Create your models here.


class User(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    company_name = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=100, null=True)
    company_url = models.CharField(max_length=100, null=True, blank=True)
    linkedin_url = models.URLField(null=True, blank=True)
    youtube_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"



class UserSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    competitors = models.JSONField(default=list)
    linkedin = models.JSONField(default=list)
    references = models.JSONField(default=list)
    youtube = models.JSONField(default=list)

    def __str__(self):
        return f"Sources for {self.user.email}"
    
    
class UserTrends(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    titre = models.CharField(max_length=255)
    lien = models.URLField()
    date = models.CharField(max_length=255)
    main_topics = models.CharField(max_length=255)
    topics_secondaires = models.CharField(max_length=255)
    mots_cles = models.TextField()
    resume = models.TextField()

    def __str__(self):
        return f"Trend for {self.user.name}: {self.titre}"
    

class Article(models.Model):
    title = models.CharField(max_length=200)
    base_content = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True)
    user_comment = models.TextField(blank=True, null=True)  # Ajouter le champ user_comment
    tone_of_voice = models.CharField(max_length=50)
    content_goal = models.CharField(max_length=200)
    language = models.CharField(max_length=50)
    goals = models.CharField(max_length=200, null=True, default="")
    content_size = models.CharField(max_length=200, null=True, default="")
    email = models.EmailField(max_length=254, default='')


