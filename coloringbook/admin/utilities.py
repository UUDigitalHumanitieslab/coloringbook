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
        
        >>> import coloringbook.testing as t, coloringbook.models as m
        >>> site = t.get_fixture_app()
        >>> # using the decorator
        >>> @site.route('/doctest')
        ... @csvdownload
        ... def simpletest (self):
        ...     m.db.session.add(m.Color(code='#888', name='grey'))
        ...     m.db.session.commit()
        ...     query = m.db.session.query(m.Color.code, m.Color.name)
        ...     return query, ['code', 'name'], 'doctest'
        >>> # inspecting what the decorated view function does
        >>> with site.app_context():
        ...     testresponse = simpletest(0)
        >>> testresponse
        <Response 22 bytes [200 OK]>
        >>> testresponse.get_data()
        'code;name\r\n#888;grey\r\n'
        >>> testresponse.mimetype
        u'text/csv'
        >>> testresponse.headers['Content-Disposition']
        u'attachment; filename="..._doctest_.csv"'
    """

    def wrap (self = None):
        query, headers, filename_core = view(self)
        if self:
            filters = filters_from_request(self)
            for f, v in filters:
                query = f.apply(query, v)
        buffer = StringIO.StringIO(b'')
        writer = csv.writer(buffer, delimiter = ';')
        writer.writerow(headers)
        writer.writerows(query.all())
        filename = '{}_{}_{}.csv'.format(
            dt.datetime.utcnow().strftime('%y%m%d%H%M'),
            filename_core,
            request.query_string if self else '' )
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
        >>> from coloringbook.admin.views import FillView
        >>> testapp = t.get_fixture_app()
        >>> s = cb.models.db.session
        >>> with testapp.test_request_context('?flt1_22=rode'):
        ...     cb.admin.utilities.filters_from_request(FillView(s))
        [(<flask_admin.contrib.sqla.filters.FilterEqual object at 0x...>, u'rode')]
    """
    
    filters = self._get_list_extra_args()[4]
    applicables = []

    if filters and self._filters:
        for idx, value in filters:
            flt = self._filters[idx]
            applicables.append((flt, value))
    
    return applicables
