from django.db import models
from django.contrib.auth.models import User

class Session(models.Model):
    SESSION_TYPES = [
        ('cafeInMaude', 'CafeInMaude'),
        ('CITP', 'CITP'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user who created the session
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='CITP')
    created_at = models.DateTimeField(auto_now_add=True)       # Timestamp when the session was created
    updated_at = models.DateTimeField(auto_now=True)           # Timestamp when the session was last updated
    file_path = models.CharField(max_length=255, blank=True, null=True)  # Path to the .maude file (optional)

    def __str__(self):
        return f"Session {self.id} for {self.user.username}"

class Command(models.Model):
    session = models.ForeignKey(Session, related_name='commands', on_delete=models.CASCADE)
    input_text = models.TextField()  # The Maude command input
    output_text = models.TextField()  # The output from Maude
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the command was issued

    def __str__(self):
        return f"Command {self.id} in session {self.session.id}"

class File(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255)  # Path to the .maude file used for the session

    def __str__(self):
        return f"File for session {self.session.id}"
