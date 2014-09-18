# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Logic and boilerplate code for custom WTForms form fields.
    
    Please refer to the WTForms documentation for details.
"""

from wtforms import fields, widgets
from flask.ext.admin._compat import text_type, as_unicode

class Select2MultipleWidget(widgets.HiddenInput):
    """
        Render a ``<input type="hidden">`` field with metadata.

        This is used to accomodate for sortable Select2 form input
        fields.

        By default, the `_value()` method will be called upon the
        associated field to provide the ``value=`` HTML attribute.
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-choices', self.json_choices(field))
        return super(Select2MultipleWidget, self).__call__(field, **kwargs)
    
    @staticmethod
    def json_choices (field):
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
    
    def _value (self):
        return ','.join(map(str, self.data))
