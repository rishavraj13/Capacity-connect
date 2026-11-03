"""Leave publication and author identity outside editable content fields."""

from django import forms

from apps.announcements.constants import BODY_MAX_LENGTH
from apps.announcements.models import Announcement


class AnnouncementForm(forms.ModelForm):
    """Bound manual text/category input before the service revalidates it."""

    class Meta:
        """Allow only manual descriptive content changes."""

        model = Announcement
        fields = ("title", "body", "category")
        help_texts = {"body": f"Maximum {BODY_MAX_LENGTH} characters."}
