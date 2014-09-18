# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Helper functions for various purposes.
"""

from flask import make_response

def csvdownload (view):
    r"""
        View decorator adding suitable response headers for CSV downloads.
        
        Use this inside a view decorator. Example:
        
        >>> import coloringbook.testing as t
        >>> site = t.get_fixture_app()
        >>> # using the decorator
        >>> @site.route('/doctest')
        ... @csvdownload
        ... def simpletest (self):
        ...     return 'name,phone\nAlice,1234567', 'doctest.csv'
        >>> # inspecting what the decorated view function does
        >>> with site.app_context():
        ...     testresponse = simpletest(0)
        >>> testresponse
        <Response 24 bytes [200 OK]>
        >>> testresponse.get_data()
        'name,phone\nAlice,1234567'
        >>> testresponse.mimetype
        u'text/csv'
        >>> testresponse.headers['Content-Disposition']
        u'attachment; filename="doctest.csv"'
    """

    def wrap (self):
        data, filename = view(self)
        response = make_response(data)
        response.headers['Cache-Control'] = 'max-age=600'
        response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response
    return wrap
