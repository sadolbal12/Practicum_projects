from django.db.models import BooleanField, Exists, OuterRef, Value

from recipes.models import Favorite, ShoppingCart


def annotate_recipe_user_flags(queryset, user):
    """Аннотации is_favorited и is_in_shopping_cart для queryset рецептов."""
    if user is not None and user.is_authenticated:
        favorited = Favorite.objects.filter(
            recipe_id=OuterRef('pk'),
            user_id=user.pk,
        )
        in_cart = ShoppingCart.objects.filter(
            recipe_id=OuterRef('pk'),
            user_id=user.pk,
        )
        return queryset.annotate(
            is_favorited=Exists(favorited),
            is_in_shopping_cart=Exists(in_cart),
        )
    return queryset.annotate(
        is_favorited=Value(False, output_field=BooleanField()),
        is_in_shopping_cart=Value(False, output_field=BooleanField()),
    )
