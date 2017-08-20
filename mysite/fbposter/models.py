from django.db import models
from django.utils import timezone
from django.conf import settings


# Create your models here.

class Tag(models.Model):
	slug = models.SlugField(max_length=200, unique=True)

	def __str__(self):
		return self.slug

class EntryQuerySet(models.QuerySet):
	def public(self):
		return self.filter(public=True)
	def by_user(self, user):
		return self.filter(author=user)

class Entry(models.Model):
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
	title=models.CharField(max_length=200)
	body=models.TextField()
	slug=models.SlugField(max_length=200, unique=True)
	public = models.BooleanField(default=True)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

	tags = models.ManyToManyField(Tag)

	objects = EntryQuerySet.as_manager()

	post_to_fb = models.BooleanField(default=False)
	post_to_fb_public = models.BooleanField(default=True)
	post_to_fb_date = models.DateTimeField(blank=True, null=True)
	post_to_fb_id = models.CharField(max_length=200, null=True)

	def __str__(self):
		return self.title

	def publish_to_fb(self):
		self.publish_to_fb = True;
		self.publish_to_fb_date = timezone.now();
		self.save()

	class Meta:
		verbose_name = "Blog Entry"
		verbose_name_plural = "Blog Entries"
		ordering = ["-created"]
