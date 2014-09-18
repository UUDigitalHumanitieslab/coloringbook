# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Helper functions for various purposes.
"""

import StringIO, csv, datetime as dt

from flask import make_response, request

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
        query, headers, filename_core = view(self)
        filters = filters_from_request(self)
        for f, v in filters:
            query = f.apply(query, v)
        buffer = StringIO.StringIO(b'')
        writer = csv.writer(buffer)
        writer.writerow(headers)
        writer.writerows(query.all())
        filename = '{}_{}_{}.csv'.format(
            dt.datetime.utcnow().strftime('%y%m%d%H%M'),
            filename_core,
            request.query_string )
        response = make_response(buffer.getvalue())
        response.headers['Cache-Control'] = 'max-age=600'
        response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response
    return wrap

def filters_from_request (self):
    """
        Parse the request arguments and return flask-admin Filter objects.
        
        This is an extract from flask-admin sqla.ModelView.get_list.
        Example of usage:
        
        >>> import coloringbook as cb, coloringbook.testing as t
        >>> testapp = t.get_fixture_app()
        >>> s = cb.models.db.session
        >>> with testapp.test_request_context('?flt1_22=rode'):
        ...     cb.admin.utilities.filters_from_request(FillView(s))
        [(<flask_admin.contrib.sqla.filters.FilterLike object at 0x...>, u'rode')]
    """
    
    filters = self._get_list_extra_args()[4]
    applicables = []

    if filters and self._filters:
        for idx, value in filters:
            flt = self._filters[idx]
            applicables.append((flt, value))
    
    return applicables
