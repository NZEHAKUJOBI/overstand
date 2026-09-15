"""
Media Management Forms - IPAWAS Platform
=========================================

Forms for file uploads and folder management.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import FileInput

from media_app.models import MediaFile, MediaFolder


class MultipleFileInput(FileInput):
    allow_multiple_selected = True


class FolderCreateForm(forms.ModelForm):
    """Form for creating custom folders"""

    class Meta:
        model = MediaFolder
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter folder name",
                    "maxlength": "100",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional folder description",
                    "rows": "3",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.member_state = kwargs.pop("member_state", None)
        self.parent = kwargs.pop("parent", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Validate folder name uniqueness"""
        name = self.cleaned_data["name"]

        # Check for existing folder with same name in same location
        existing = MediaFolder.objects.filter(
            member_state=self.member_state, parent=self.parent, name__iexact=name, is_deleted=False
        )

        if existing.exists():
            raise ValidationError(f"A folder named '{name}' already exists in this location.")

        return name


class FolderRenameForm(forms.Form):
    """Form for renaming folders"""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter new folder name"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.folder = kwargs.pop("folder")
        super().__init__(*args, **kwargs)
        self.fields["name"].initial = self.folder.name

    def clean_name(self):
        """Validate new folder name"""
        name = self.cleaned_data["name"]

        # Check for system folder
        if self.folder.is_system:
            raise ValidationError("System folders cannot be renamed.")

        # Check for duplicate
        existing = MediaFolder.objects.filter(
            member_state=self.folder.member_state,
            parent=self.folder.parent,
            name__iexact=name,
            is_deleted=False,
        ).exclude(pk=self.folder.pk)

        if existing.exists():
            raise ValidationError(f"A folder named '{name}' already exists in this location.")

        return name


class FileUploadForm(forms.Form):
    """Form for single file upload"""

    file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control", "accept": "*/*"}))

    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Optional: Custom file name"}
        ),
        help_text="Leave blank to use original filename",
    )

    alt_text = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Alt text (for images, SEO)"}
        ),
        help_text="Recommended for images",
    )

    caption = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Optional file description or caption",
                "rows": "2",
            }
        ),
    )

    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter tags separated by commas"}
        ),
        help_text="e.g., project, annual-report, 2024",
    )

    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags_str = self.cleaned_data.get("tags", "")
        if not tags_str:
            return []

        # Split by comma and clean up
        tags = [tag.strip() for tag in tags_str.split(",")]
        tags = [tag for tag in tags if tag]  # Remove empty tags

        return tags


class BulkFileUploadForm(forms.Form):
    """Form for bulk file upload"""

    files = forms.FileField(
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": "*/*",
            }
        ),
        required=True,
        help_text="You can select multiple files at once",
    )


class FileEditForm(forms.ModelForm):
    """Form for editing file metadata"""

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter tags separated by commas"}
        ),
        help_text="e.g., project, annual-report, 2024",
    )

    class Meta:
        model = MediaFile
        fields = ["name", "alt_text", "caption"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "File name"}),
            "alt_text": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Alt text (for images, SEO)"}
            ),
            "caption": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "File description or caption",
                    "rows": "3",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.tags:
            self.fields["tags_input"].initial = ", ".join(self.instance.tags)

    def clean_tags_input(self):
        """Convert comma-separated tags to list"""
        tags_str = self.cleaned_data.get("tags_input", "")
        if not tags_str:
            return []

        tags = [tag.strip() for tag in tags_str.split(",")]
        tags = [tag for tag in tags if tag]

        return tags

    def save(self, commit=True):
        """Save with tags"""
        instance = super().save(commit=False)
        instance.tags = self.cleaned_data.get("tags_input", [])

        if commit:
            instance.save()

        return instance


class FileMoveForm(forms.Form):
    """Form for moving files to different folder"""

    target_folder = forms.ModelChoiceField(
        queryset=MediaFolder.objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Select destination folder",
    )

    def __init__(self, *args, **kwargs):
        self.member_state = kwargs.pop("member_state")
        self.current_folder = kwargs.pop("current_folder", None)
        super().__init__(*args, **kwargs)

        # Populate folder choices
        folders = MediaFolder.objects.filter(
            member_state=self.member_state, is_deleted=False
        ).exclude(folder_type="root")

        # Exclude current folder
        if self.current_folder:
            folders = folders.exclude(pk=self.current_folder.pk)

        self.fields["target_folder"].queryset = folders


class FileSearchForm(forms.Form):
    """Form for searching files"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search files...", "autocomplete": "off"}
        ),
    )

    file_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + MediaFile.FILE_TYPES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    folder = forms.ModelChoiceField(
        queryset=MediaFolder.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self.member_state = kwargs.pop("member_state")
        super().__init__(*args, **kwargs)

        # Populate folder choices
        self.fields["folder"].queryset = MediaFolder.objects.filter(
            member_state=self.member_state, is_deleted=False
        )
