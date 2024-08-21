from django.contrib import admin
from .models import Session, Command

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username',)

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'input_text', 'output_text', 'timestamp')
    search_fields = ('session__id', 'input_text')
