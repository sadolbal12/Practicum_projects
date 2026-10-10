from http import HTTPStatus

from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthenticatedAuthorOrReadOnly
from api.querysets import annotate_recipe_user_flags
from api.serializers.recipe import (IngredientSerializer,
                                    RecipeCreateUpdateSerializer,
                                    RecipeMinifiedSerializer,
                                    RecipeReadSerializer, TagSerializer)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для тегов (только чтение, доступно всем)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    authentication_classes = ()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиента с фильтрацией через istartswith."""

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    authentication_classes = ()

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    queryset = Recipe.objects.all()
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.all()
        return annotate_recipe_user_flags(queryset, self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in (
            'favorite', 'delete_favorite',
            'shopping_cart', 'delete_shopping_cart',
            'download_shopping_cart', 'create',
        ):
            return (IsAuthenticated(),)
        return (IsAuthenticatedAuthorOrReadOnly(),)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=HTTPStatus.CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_recipe_relation(
            self, request, related_name,
            success_serializer=RecipeMinifiedSerializer):
        """Обработчик добавления/удаления рецепта в избранное или корзину."""
        recipe = self.get_object()
        user = request.user
        related = getattr(recipe, related_name)

        if request.method == 'POST':
            _obj, created = related.get_or_create(user=user)
            if created:
                serializer = success_serializer(
                    recipe, context={'request': request},
                )
                return Response(
                    serializer.data,
                    status=HTTPStatus.CREATED,
                )
            return Response(
                {'detail': 'Уже добавлено'},
                status=HTTPStatus.BAD_REQUEST,
            )

        deleted, _ = related.filter(user_id=user.pk).delete()
        if deleted:
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {'detail': 'Не найдено'},
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_recipe_relation(request, 'in_shopping_cart')

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._handle_recipe_relation(request, 'in_shopping_cart')

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._handle_recipe_relation(request, 'favorited_by')

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._handle_recipe_relation(request, 'favorited_by')

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user
        cart_recipe_ids = user.shopping_cart.values_list(
            'recipe_id', flat=True
        )
        aggregated = RecipeIngredient.objects.filter(
            recipe_id__in=cart_recipe_ids,
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total_amount=Sum('amount'),
        ).order_by('ingredient__name')

        content = '\n'.join(
            self._format_shopping_line(row)
            for row in aggregated
        )
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @staticmethod
    def _format_shopping_line(row):
        name = row['ingredient__name']
        unit = row['ingredient__measurement_unit']
        amount = row['total_amount']
        return f'{name} ({unit}) – {amount}'

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        path = reverse(
            'recipe-short-link',
            kwargs={'recipe_id': recipe.pk},
        )
        short_link = request.build_absolute_uri(path)
        return Response({'short-link': short_link})
