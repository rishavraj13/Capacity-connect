"""Keep subject choice on declaration only and exclude ownership inputs."""

from django import forms

from apps.catalog.selectors import active_subjects
from apps.competency.models import TrainerCompetency


class CompetencyForm(forms.ModelForm):
    """Limit existing declaration edits to the two permitted values."""

    class Meta:
        """Exclude immutable subject and trainer fields from update forms."""

        model = TrainerCompetency
        fields = ("proficiency", "years_experience")


class DeclarationForm(CompetencyForm):
    """Only show currently active subjects when declaring a new competency."""

    subject = forms.ModelChoiceField(queryset=active_subjects())


class RankingForm(forms.Form):
    """Allow Admin to inspect active or retired-subject rankings explicitly."""

    subject = forms.ModelChoiceField(queryset=active_subjects().none(), required=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Keep subject reads in the catalog selector boundary."""
        from apps.catalog.selectors import all_subjects

        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = all_subjects()
