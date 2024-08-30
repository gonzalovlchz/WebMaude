from django.db import models
from django.contrib.auth.models import User
from django.utils.deconstruct import deconstructible
import uuid
import os

class Session(models.Model):
    SESSION_TYPES = [
        ('cafeInMaude', 'CafeInMaude'),
        ('CITP', 'CITP'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user who created the session
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='CITP')
    created_at = models.DateTimeField(auto_now_add=True)       # Timestamp when the session was created
    updated_at = models.DateTimeField(auto_now=True)           # Timestamp when the session was last updated

    def __str__(self):
        return f"Session {self.id} for {self.user.username}"

class Command(models.Model):
    session = models.ForeignKey(Session, related_name='commands', on_delete=models.CASCADE)
    input_text = models.TextField()  # The Maude command input
    output_text = models.TextField()  # The output from Maude
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the command was issued

    def __str__(self):
        return f"Command {self.id} in session {self.session.id}"

@deconstructible
class UniqueUploadTo:
    def __init__(self, upload_to):
        self.upload_to = upload_to

    def __call__(self, instance, filename):
        # Generate a unique filename using UUID
        ext = filename.split('.')[-1]  # Extract file extension
        unique_filename = f"{uuid.uuid4()}.{ext}"  # Create a unique filename
        return os.path.join(self.upload_to, unique_filename)

class ExampleFile(models.Model):
    name = models.CharField(max_length=255, null=True)  # The name of the file
    maude = models.FileField(null=True, blank=True, upload_to=UniqueUploadTo('uploads/maude'))  # Unique filenames for Maude files
    program = models.FileField(null=True, blank=True, upload_to=UniqueUploadTo('uploads/program'))  # Unique filenames for Program files
    session_type = models.CharField(max_length=20, choices=Session.SESSION_TYPES, default='CITP')  # Session type for filtering

    def __str__(self):
        return f"ExampleFile {self.name} with session type {self.session_type}"
    
class SiteSetting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Settings cannot be deleted. Please edit the setting instead.")

    @classmethod
    def get_setting(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value):
        setting, created = cls.objects.get_or_create(key=key)
        setting.value = value
        setting.save()
        return setting