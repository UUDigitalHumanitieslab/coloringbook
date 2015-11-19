# Coloringbook -- current version #

## 1.2 ##

Update and enhancement release.

  * pip requirements are pinned using `pip-compile`.
  * All external dependencies were updated.
  * Application can now be served from a non-root location (e.g. under
    yourdomain.edu/coloringbook/)
  * Sounds can be replayed with a button.
  * Sounds should play more reliably on iPad.


# Version history #

## 1.1 ##

A few small but important improvements:

  * Addition of a privacy statement.
  * Addition of a favicon and an application icon for the iPad.
  * Use of the mousedown event instead of the click event, for faster 
    response on touch devices.
  * Font size adjustments.


## 1.0.1 ##

Small bugfix and enhancement release. Changes:

  * Spaces in area names are automatically changed into underscores, in
    order to prevent the issue where expectations are not pre-rendered in
    the expectation editing form.
  * Non-simultaneous sentences are displayed for six seconds instead of
    three.
  * Simultaneous sentences are removed before the final evaluation form
    is shown.


## 1.0 ##

The finished application, ready for deployment.

Additions and improvements in this version: more documentation,
including a visual representation of the database layout and a short
manual in the admin interface, license terms, a subjects tab in the
admin interface with export option, filtering subjects by ID, and
removal of the coloringbook harness from the domain root.


## 0.3b1 ##

This hotfix release fixes some issues that caused the application to
work in Flask-SQLAlchemy version 0.16, but not in version 1.0.


## 0.3b ##

This beta release is complete enough to be usable in principle. Apart
from some dots and crosses, the only functionality that is still
really missing is an admin model view of subjects with export options.

Additions and improvements in this version: restriction of editing
capabilities in the Color and Language admin model views, strongly
improved and extended CSV export, possibility to display a sentence
simultaneously with the drawing, better modularity of admin templates,
explicit usage of the InnoDB engine for all database tables, addition
of the evaluation form, better scaling of the drawing to fit the
viewport, authentic instructions and form texts, and dynamic fetching
of surveys by URL.


## 0.2a ##

This alpha release adds improved documentation with doctest, a
minimalist testing infrastructure, improved configuration handling,
more customized model views, adherence to PEP 257, the possibility to
edit drawings, pages and page expectations from the admin interface,
uploading of sound recordings, a File abstraction that both Drawing
and Sound ORMs derive from, and better colors.


## 0.1a ##

This alpha release contains the necessary infrastructure to enable
deployment on an Apache server. It also implements most of the
application functionality. Still lacking are the possibility to define
pages for custom drawings, as well as the possibility to serve
customized surveys to test subjects.
