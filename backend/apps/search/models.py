from django.db import models
from django.utils.translation import gettext_lazy as _


class SearchSynonym(models.Model):
    """Words that should find each other: «пасат» ↔ «passat», «фара» ↔ «оптика»."""

    term = models.CharField(_("слово"), max_length=80, unique=True)
    synonyms = models.CharField(_("синоніми"), max_length=500, help_text=_("Через кому: passat, пассат"))
    is_active = models.BooleanField(_("активний"), default=True)

    class Meta:
        ordering = ["term"]
        verbose_name = _("синонім пошуку")
        verbose_name_plural = _("синоніми пошуку")

    def __str__(self):
        return f"{self.term} → {self.synonyms}"

    def synonym_list(self) -> list[str]:
        return [s.strip().lower() for s in self.synonyms.split(",") if s.strip()]
