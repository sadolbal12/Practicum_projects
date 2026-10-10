from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(AuthUserAdmin):
    """Админка пользователя."""

    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    fieldsets = AuthUserAdmin.fieldsets + (
        ('Аватар', {'fields': ('avatar',)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
