from django.db import models
from django.contrib.auth.models import User

class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the user who created the session
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
