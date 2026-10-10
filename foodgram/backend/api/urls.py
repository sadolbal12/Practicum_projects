from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.recipe import IngredientViewSet, RecipeViewSet, TagViewSet
from api.views.user import SubscriptionViewSet, UserViewSet

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('users', UserViewSet, basename='user')

urlpatterns = (
    path('', include(router.urls)),
    path(
        'users/<int:author_id>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
        name='user-subscribe',
    ),
)
