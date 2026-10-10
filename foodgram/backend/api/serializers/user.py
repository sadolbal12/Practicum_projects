from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from users.models import Subscription

User = get_user_model()


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password', None)
        return data


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'is_subscribed',
        )
        read_only_fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'avatar', 'is_subscribed',
        )

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return obj.following.filter(user_id=request.user.pk).exists()


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        from api.serializers.recipe import RecipeMinifiedSerializer
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionResponseSerializer(UserWithRecipesSerializer):
    class Meta(UserWithRecipesSerializer.Meta):
        pass


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()

    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError(
                'Это поле не может быть пустым.',
            )
        if value.startswith('http://') or value.startswith('https://'):
            raise serializers.ValidationError(
                'Загрузите новый файл, а не URL существующего аватара.',
            )
        if not value.startswith('data:image'):
            raise serializers.ValidationError(
                'Неверный формат. Нужен data URL '
                '(data:image/...;base64,...).',
            )
        return value


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Создание подписки на автора."""

    class Meta:
        model = Subscription
        fields = ()

    def validate(self, attrs):
        subscriber = self.context['request'].user
        author = self.context['author']
        if subscriber.pk == author.pk:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя',
            )
        if author.following.filter(user_id=subscriber.pk).exists():
            raise serializers.ValidationError('Вы уже подписаны')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        author = self.context['author']
        return Subscription.objects.create(user=user, author=author)


class UnsubscribeSerializer(serializers.Serializer):
    """Проверка перед отменой подписки."""

    def validate(self, attrs):
        subscriber = self.context['request'].user
        author = self.context['author']
        if not author.following.filter(user_id=subscriber.pk).exists():
            raise serializers.ValidationError('Вы не были подписаны')
        return attrs
