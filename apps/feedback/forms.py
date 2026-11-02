"""Expose only rating/comment, leaving ownership to selectors and services."""

from django import forms

from apps.feedback.constants import MAX_COMMENT_LENGTH, MAX_RATING, MIN_RATING
from apps.feedback.models import Feedback


class FeedbackForm(forms.ModelForm):
    """Bound human input without allowing author or target reassignment."""

    rating = forms.IntegerField(min_value=MIN_RATING, max_value=MAX_RATING)
    comment = forms.CharField(
        max_length=MAX_COMMENT_LENGTH, required=False, widget=forms.Textarea
    )

    class Meta:
        """Keep target and author outside mass assignment."""

        model = Feedback
        fields = ("rating", "comment")
