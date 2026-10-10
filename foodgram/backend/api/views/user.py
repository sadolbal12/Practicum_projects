import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers.user import (AvatarSerializer,
                                  SubscriptionCreateSerializer,
                                  SubscriptionResponseSerializer,
                                  UnsubscribeSerializer, UserCreateSerializer,
                                  UserSerializer, UserWithRecipesSerializer)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer

    def get_permissions(self):
        public_actions = ('create', 'list', 'retrieve')
        if self.action in public_actions:
            return (AllowAny(),)
        return (IsAuthenticated(),)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        author_ids = user.follower.values_list('author_id', flat=True)
        authors = User.objects.filter(
            pk__in=author_ids,
        ).prefetch_related('recipes')

        page = self.paginate_queryset(authors)

        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            authors, many=True, context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def me_avatar(self, request):
        if request.method == 'DELETE':
            return self._delete_avatar(request)
        return self._set_avatar(request)

    def _set_avatar(self, request):
        user = request.user
        avatar_file = request.FILES.get('avatar')

        if avatar_file:
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = avatar_file
            user.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data['avatar']

        if user.avatar:
            user.avatar.delete(save=False)
        header, imgstr = avatar_data.split(';base64,', 1)
        ext = header.split('/')[-1].split('+')[0]
        if ext == 'jpeg':
            ext = 'jpg'
        unique_id = uuid.uuid4()
        user_id = user.id
        file_name = f'avatar_{user_id}_{unique_id}.{ext}'
        file_data = ContentFile(
            base64.b64decode(imgstr),
            name=file_name,
        )
        user.avatar.save(file_data.name, file_data, save=True)
        avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    def _delete_avatar(self, request):
        user = request.user
        if not user.avatar:
            raise NotFound('Аватар не установлен.')
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def _get_author(self, author_id):
        return get_object_or_404(User, id=author_id)

    def create(self, request, author_id=None):
        author = self._get_author(author_id)
        serializer = SubscriptionCreateSerializer(
            data={},
            context={'request': request, 'author': author},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = SubscriptionResponseSerializer(
            author, context={'request': request},
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, author_id=None):
        user = request.user
        author = self._get_author(author_id)
        serializer = UnsubscribeSerializer(
            data={},
            context={'request': request, 'author': author},
        )
        serializer.is_valid(raise_exception=True)
        author.following.filter(user_id=user.pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
