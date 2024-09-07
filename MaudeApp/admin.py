from django.contrib import admin
from .models import Session, Command, ExampleFile, SiteSetting  # Import the File model
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_type', 'name', 'created_at', 'updated_at')  # Added session_type to display
    search_fields = ('user__username', 'session_type')  # Added session_type to search

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'input_text', 'output_text', 'timestamp')
    search_fields = ('session__id', 'input_text')

@admin.register(ExampleFile)
class ExampleFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'session_type', 'maude', 'program')
    search_fields = ('name', 'session_type')

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)

    def has_delete_permission(self, request, obj=None):
        # Disable delete permission in admin
        return False
    
def approve_user(modeladmin, request, queryset):
    queryset.update(is_active=True)

approve_user.short_description = "Approve selected users"

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    actions = [approve_user]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)