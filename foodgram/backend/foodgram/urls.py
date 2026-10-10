from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from recipes.short_link import ShortLinkRedirectView

auth_urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]

api_urlpatterns = [
    path('', include('api.urls')),
    path(
        'users/set_password/',
        RedirectView.as_view(
            url='/api/auth/users/set_password/', permanent=False,
        ),
        name='user-set-password',
    ),
    path('auth/', include(auth_urlpatterns)),
]

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        ShortLinkRedirectView.as_view(),
        name='recipe-short-link',
    ),
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,
    )
