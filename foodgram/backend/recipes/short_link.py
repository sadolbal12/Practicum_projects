from django.shortcuts import redirect
from django.views import View


class ShortLinkRedirectView(View):
    """Редирект /s/<id>/ → /recipes/<id> для короткой ссылки из API."""

    def get(self, request, recipe_id):
        recipe_path = '/recipes/{recipe_id}'.format(recipe_id=recipe_id)
        return redirect(recipe_path, permanent=False)
