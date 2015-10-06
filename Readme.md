Coloringbook
============

A web-based coloringbook survey application
by Digital Humanities Lab, Utrecht University


Why does it exist?
------------------

Because it allows researchers to test how subjects parse language, without revealing the intent of the study. Moreover, it is a natural task for test subjects that doesn't make them *feel* like they are being tested. It is designed to work well on tablet devices, in order to accomodate for very young subjects.


What does it do?
----------------

Test subjects are presented with a subscription form, instructions, a series of coloringbook pages and finally an evaluation form. After both forms have been completed and all pages have been colored, all data are submitted to the server at once.

When a coloringbook page is presented, initially a sentence is displayed, in written text, sound or both. Then, the drawing is shown and the subject is given the means to pick colors and fill areas of the drawing by point-and-click. The researcher may also opt to offer the sentence simultaneously with the drawing. This also works on touch devices. All data for the coloringbook pages are downloaded to the client side at once before the survey starts.

On the server side, all coloring data are collected in a table that can be filtered by survey, page, area and subject. Each individual fill action is recorded with the color and the exact elapsed time since the drawing appeared on screen. Researchers can also define expected results for each page and compare the data with their expectations. Tables can be exported to CSV for further processing in any spreadsheet or statistics software.

Researchers can compose their own surveys with custom images and sounds. The surveys are made available to test subjects through a fixed URL.


How to deploy?
--------------

On the client side, test subjects just need to run a HTML5 capable browser.

On the server side, Coloringbook is a WSGI application, which means that it will run on any webserver that supports standard Python web applications. An example configuration file for Apache with mod_wsgi is included. Apart from a WSGI-enabled webserver, install the dependencies using `pip install -r requirements.txt`.

Assuming you opt to use MySQL (or anything other than SQLite), you need to create an empty database with pre-configured access rights for the Coloringbook application to use. For example by entering the following commands while running `mysql` as root user:

    create database coloringbook;
    grant all privileges on coloringbook.* to 'coloringbook'@'localhost' identified by 'myawesomepassword';

**Note** that you should not use the password quoted above. You can choose the name of the database and the name of the user freely as well.

Coloringbook obtains the necessary information to connect to the database from a user-provided configuration file. This is what the file contents should minimally look like:

    SQLALCHEMY_DATABASE_URI = 'mysql://coloringbook:myawesomepassword@localhost/coloringbook'
    SECRET_KEY = '12345678901234567890'

This file should be saved with a `.py` extension. The WSGI script should import this module and pass it as the only argument to coloringbook.create_app. Please refer to the example WSGI script for details.

To use Coloringbook with Apache and mod_wsgi, copy, rename and edit the `apache-template.conf` file to suit your needs and insert your edited version into the `conf.d` subdirectory of wherever Apache happens to be installed on your server. Your application will be running after you restart Apache.

The application does not take care of authentication or authorization. You should configure this directly on the webserver by restricting access to `/admin/`, for example using LDAP.

For development, you may run a local test server by invoking the included `run.py` script. This will also switch on debugging settings. It does not require Apache or any other proper webserver. The application will run on `localhost:5000`.


Development
-----------

An overview of the database layout is given in `Database.svg`. For the complete specification, refer to `coloringbook/models.py`. Anything in `admin` subfolders is specific to the admin interface. Everything else in the `coloringbook` package is involved in delivering surveys to subjects and receiving data from them. Motivations are documented throughout the code in comments; with some referencing to documentation for Flask, SQLAlchemy and jQuery, you should be able to find your way.
