from flask import make_response

def csvdownload (filename):
    ''' View decorator adding suitable response headers for CSV downloads. '''

    def decorate (view):
        def wrap (self):
            response = make_response(view(self))
            response.headers['Cache-Control'] = 'max-age=600'
            response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            return response
        return wrap

    return decorate
