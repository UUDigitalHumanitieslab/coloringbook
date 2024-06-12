# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    Logic and boilerplate code for custom WTForms form fields and validators.

    Please refer to the WTForms documentation for details.
"""

from wtforms import fields, widgets
from wtforms.validators import ValidationError, Length
from flask.ext.admin._compat import text_type, as_unicode


class Select2MultipleWidget(widgets.HiddenInput):
    """
        Render a ``<input type="hidden">`` field with metadata.

        This is used to accomodate for sortable Select2 form input
        fields.

        By default, the `_value()` method will be called upon the
        associated field to provide the ``value=`` HTML attribute.
    """

    input_type = 'select2multiple'  # see flask-admin issue #511

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-choices', self.json_choices(field))
        kwargs.setdefault('type', 'hidden')  # see flask-admin issue #511
        return super(Select2MultipleWidget, self).__call__(field, **kwargs)

    @staticmethod
    def json_choices(field):
        objects = ('{{"id": {}, "text": "{}"}}'.format(*c) for c in field.iter_choices())
        return '[' + ','.join(objects) + ']'


class Select2MultipleField(fields.SelectMultipleField):
    """
        `Select2 <https://github.com/ivaynberg/select2>`_ styled select widget.

        You must include select2.js, form.js and select2 stylesheet for it to
        work.

        This is a slightly altered derivation of the original Select2Field.
    """
    widget = Select2MultipleWidget()

    def __init__(self, label=None, validators=None, coerce=text_type,
                choices=None, allow_blank=False, blank_text=None, **kwargs):
        super(Select2MultipleField, self).__init__(
            label, validators, coerce, choices, **kwargs
        )
        self.allow_blank = allow_blank
        self.blank_text = blank_text or ' '

    def iter_choices(self):
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is [])

        for value, label in self.choices:
            yield (value, label, self.coerce(value) in self.data)

    def process_data(self, value):
        if not value:
            self.data = []
        else:
            try:
                self.data = []
                for v in value:
                    self.data.append(self.coerce(v[0]))
            except (ValueError, TypeError):
                self.data = []

    def process_formdata(self, valuelist):
        if valuelist:
            if valuelist[0] == '__None':
                self.data = []
            else:
                try:
                    self.data = []
                    for value in valuelist[0].split(','):
                        self.data.append(self.coerce(value))
                except ValueError:
                    raise ValueError(self.gettext(u'Invalid Choice: could not coerce {}'.format(value)))

    def pre_validate(self, form):
        if self.allow_blank and self.data is []:
            return

        super(Select2MultipleField, self).pre_validate(form)

    def _value(self):
        return ','.join(map(str, self.data))


class FileNameLength(Length):
    """
    Validates the length of a file name.
    """
    def get_length(self, form, field):
        return field.data and len(field.data.filename) or 0

    # If WTForms adopts our changes, this method need not be overridden anymore.
    def __call__(self, form, field):
        l = self.get_length(form, field)
        if l < self.min or self.max != -1 and l > self.max:
            message = self.message
            if message is None:
                if self.max == -1:
                    message = field.ngettext('Field must be at least %(min)d character long.',
                                            'Field must be at least %(min)d characters long.', self.min)
                elif self.min == -1:
                    message = field.ngettext('Field cannot be longer than %(max)d character.',
                                            'Field cannot be longer than %(max)d characters.', self.max)
                else:
                    message = field.gettext('Field must be between %(min)d and %(max)d characters long.')

            raise ValidationError(message % dict(min=self.min, max=self.max, length=l))
