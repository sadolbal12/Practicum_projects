from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)

    def favorite_count(self, obj):
        return obj.favorited_by.count()
    favorite_count.short_description = 'В избранном'
    readonly_fields = ('favorite_count',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeRelationAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeRelationAdmin):
    pass
