from django.contrib import admin
from .models import Session, Command, ExampleFile  # Import the File model

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_type', 'created_at', 'updated_at')  # Added session_type to display
    search_fields = ('user__username', 'session_type')  # Added session_type to search

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'input_text', 'output_text', 'timestamp')
    search_fields = ('session__id', 'input_text')

@admin.register(ExampleFile)
class ExampleFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'session_type', 'maude', 'program')
    search_fields = ('name', 'session_type')