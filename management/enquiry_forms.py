from django import forms

from pages.models import ContactEnquiry


class EnquiryReviewForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ("status", "follow_up_at", "internal_notes")
        widgets = {
            "follow_up_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "internal_notes": forms.Textarea(attrs={"rows": 5}),
        }
