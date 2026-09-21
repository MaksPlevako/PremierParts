from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action

from . import index
from .models import SearchSynonym


@admin.register(SearchSynonym)
class SearchSynonymAdmin(ModelAdmin):
    list_display = ("term", "synonyms", "is_active")
    list_editable = ("synonyms", "is_active")
    search_fields = ("term", "synonyms")
    actions_list = ["reindex"]

    @action(description=_("Переіндексувати пошук"), icon="sync", url_path="reindex")
    def reindex(self, request):
        try:
            total = index.reindex_all()
            self.message_user(request, _("Проіндексовано товарів: %d") % total, messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, _("Пошуковий сервер недоступний: %s") % exc, messages.ERROR)
        return redirect(reverse_lazy("admin:search_searchsynonym_changelist"))
