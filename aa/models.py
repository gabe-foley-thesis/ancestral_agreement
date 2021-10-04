from werkzeug.datastructures import FileStorage
from wtforms import ValidationError, fields
from wtforms.validators import required
from wtforms.widgets import FileInput
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    FileField,
    SelectMultipleField,
    StringField,
)
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired
from gettext import gettext


class BlobUploadField(fields.StringField):
    widget = FileInput()

    def __init__(
        self,
        label=None,
        allowed_extensions=None,
        size_field=None,
        filename_field=None,
        mimetype_field=None,
        **kwargs
    ):

        self.allowed_extensions = allowed_extensions
        self.size_field = size_field
        self.filename_field = filename_field
        self.mimetype_field = mimetype_field
        validators = [required()]

        super(BlobUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        """
        Check if file extension is allowed.

        :param filename:
            File name to check
        """
        if not self.allowed_extensions:
            return True

        return "." in filename and filename.rsplit(".", 1)[1].lower() in map(
            lambda x: x.lower(), self.allowed_extensions
        )

    def _is_uploaded_file(self, data):
        return data and isinstance(data, FileStorage) and data.filename

    def pre_validate(self, form):
        super(BlobUploadField, self).pre_validate(form)
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(
            self.data.filename
        ):
            raise ValidationError(gettext("Invalid file extension"))

    def process_formdata(self, valuelist):
        if valuelist:
            data = valuelist[0]
            self.data = data

    def populate_obj(self, obj, name):

        if self._is_uploaded_file(self.data):

            _profile = self.data.read()
            setattr(obj, name, _profile)

            if self.size_field:
                setattr(obj, self.size_field, len(_profile))

            if self.filename_field:
                setattr(obj, self.filename_field, self.data.filename)

            if self.mimetype_field:
                setattr(obj, self.mimetype_field, self.data.content_type)


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


# Form for uploading files
class UploadForm(FlaskForm):
    name = StringField(u"Dataset name", [DataRequired()])
    tree = FileField("Tree file (must contain ancestral nodes)", [DataRequired()])
    alignment = FileField(
        "Alignment file (must contain ancestral sequences)", [DataRequired()]
    )


    upload_submit = SubmitField("Upload file")


# Form for uploading files
class StaticUploadForm(FlaskForm):
    name = StringField(u"Dataset name")
    tree = FileField("Tree file (must contain ancestral nodes)")
    alignment = FileField("Alignment file (must contain ancestral sequences)")
    name2 = StringField(u"Second dataset name")
    tree2 = FileField("Second tree file (must contain ancestral nodes)")
    alignment2 = FileField("Second alignment file (must contain ancestral sequences)")
    upload_submit = SubmitField("Upload file")
