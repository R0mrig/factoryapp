from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
# Create your models here.



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=100, null=True)
    last_name = models.CharField(_('last name'), max_length=100, null=True)
    company_name = models.CharField(_('company name'), max_length=100, null=True)
    title = models.CharField(_('title'), max_length=100, null=True)
    company_url = models.CharField(_('company url'), max_length=100, null=True, blank=True)
    linkedin_url = models.URLField(_('linkedin url'), null=True, blank=True)
    youtube_url = models.URLField(_('youtube url'), null=True, blank=True)
    password = models.CharField(_('password'), max_length=128, default='my_default_password')
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email



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
    product = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=50, null=True, default="")
    goals = models.CharField(max_length=200, null=True, default="")
    content_size = models.CharField(max_length=200, null=True, default="")
    email = models.EmailField(max_length=254, default='')
    Company_info = models.TextField(blank=True, null=True)



class Trend(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Utilisateur")
    titre = models.CharField(max_length=255, verbose_name="Titre")
    resume = models.TextField(verbose_name="Résumé")
    main_topics = models.TextField(verbose_name="Sujets Principaux")
    secondary_topics = models.TextField(verbose_name="Sujets Secondaires")
    ponderation = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Pondération")

    def __str__(self):
        return self.titre


class LinkedInPost(models.Model):
    postUrl = models.URLField(max_length=1024, verbose_name="URL du post")
    postContent = models.TextField(verbose_name="Contenu du post")
    profileUrl = models.URLField(max_length=1024, verbose_name="URL du profil")
    postDate = models.CharField(max_length=100, verbose_name="Date du post")

    def __str__(self):
        return f"Post de {self.user.email} - {self.action}"