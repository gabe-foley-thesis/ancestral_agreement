from werkzeug.datastructures import FileStorage
from wtforms import ValidationError, fields
from wtforms.validators import required
from wtforms.widgets import FileInput
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    FileField,
    SelectField,
    FieldList,
    FormField,
    TextField,
    SelectMultipleField,
    TextAreaField,
    StringField,
)
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Email
from gettext import gettext


# Create models


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
    # input_text = StringField(u'Input text', [validators.optional()])
    # type = SelectField('What type of file is this?', [validators.DataRequired()],
    #                    choices=[("protein", "FASTA (amino acids)"), ("nucleotide", "FASTA (nucleotides)"),
    #                             ("species", "Species list"), ("genome", "Genome ID list"), ("profile", "Profile")])
    # add_sequence = BooleanField("Add sequences to sequence database?", default="checked")
    # add_genome = BooleanField("Search for genomic records?", default="checked")
    # single_genome = BooleanField("Retrieve just a single record for each genome?", default="checked")
    # representative = BooleanField("If previous genome search fails, search RefSeq representative genomes",
    #                               default="checked")
    # assembly = BooleanField("If previous genome search fails, search RefSeq assembly genomes",
    #                         default="checked")
    # genbank = BooleanField("If previous genome search fails, search GenBank assembly genomes",
    #                         default="checked")
    #
    # search_shotgun = BooleanField("Search for shotgun sequenced genomes if we can't find another "
    #                               "genomic record?", default="checked")
    # genome_type = SelectField('Which genome records should we return?', choices=[
    #     ('reference genome','Retrieve RefSeq reference genome/s'),
    #     ('representative genome', 'Retrieve RefSeq representative genome/s'),
    #     ('assembly', 'Retrieve RefSeq assembly genome/s'),
    #     ('genbank', 'Retrieve GenBank assembly genome/s')])

    upload_submit = SubmitField("Upload file")


# CAUTION: Untested code ahead
class If(object):
    def __init__(self, parent, run_validation=None, extra_validators=None, msg=None):
        self.parent = parent
        self.msg = msg if msg is not None else u"Invalid"
        if callable(run_validation):
            self.run_validation = run_validation
        else:
            _run_validation = lambda self, parent, form: parent.data == run_validation
            self.run_validation = _run_validation
        self.extra_validators = extra_validators if extra_validators is not None else []

    def __call__(self, field, form):
        parent = getattr(form, self.parent)
        if self.run_validation(parent, form):
            return field.validate(form, extra_validators=self.extra_validators)


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    contact_type = SelectField(
        "Contact Type",
        validators=[DataRequired()],
        choices=[
            ("email", "Email"),
            ("phone", "Phone Number"),
            ("im", "Instant Message"),
        ],
    )
    # `If` is a custom validator - see below
    email_address = StringField(
        "Email", validators=[If("contact_type", "email", [DataRequired(), Email()])]
    )
    phone_number = StringField(
        "Phone #", validators=[If("contact_type", "phone", [DataRequired()])]
    )
    im_handle = StringField(
        "IM Handle", validators=[If("contact_type", "im", [DataRequired()])]
    )


class SignUpForm(FlaskForm):
    # Other fields go here
    contacts = FieldList(FormField(ContactForm))


# Form for uploading files
class StaticUploadForm(FlaskForm):
    name = StringField(u"Dataset name")
    tree = FileField("Tree file (must contain ancestral nodes)")
    alignment = FileField("Alignment file (must contain ancestral sequences)")
    name2 = StringField(u"Second dataset name")
    tree2 = FileField("Second tree file (must contain ancestral nodes)")
    alignment2 = FileField("Second alignment file (must contain ancestral sequences)")

    # genome_type = SelectField('Which genome records should we return?', choices=[
    #     ('reference genome','Retrieve RefSeq reference genome/s'),
    #     ('representative genome', 'Retrieve RefSeq representative genome/s'),
    #     ('assembly', 'Retrieve RefSeq assembly genome/s'),
    #     ('genbank', 'Retrieve GenBank assembly genome/s')])

    upload_submit = SubmitField("Upload file")
