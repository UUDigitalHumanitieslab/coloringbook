# Coloring Book

A web-based coloring book survey application
by Digital Humanities Lab, Utrecht University


## Why does it exist?

Because it allows researchers to test how subjects parse language, without revealing the intent of the study. Moreover, it is a natural task for test subjects that doesn't make them *feel* like they are being tested. It is designed to work well on tablet devices, in order to accomodate for very young subjects.


## What does it do?

Test subjects are presented with a subscription form, instructions, a series of coloring pages and finally an evaluation form. After both forms have been completed and all pages have been colored, all data are submitted to the server at once.

When a coloring page is presented, initially a sentence is displayed, in written text, sound or both. Then, the drawing is shown and the subject is given the means to pick colors and fill areas of the drawing by point-and-click. The researcher may also opt to offer the sentence simultaneously with the drawing. This also works on touch devices. All data for the coloring pages are downloaded to the client side at once before the survey starts.

On the server side, all coloring data are collected in a table that can be filtered by survey, page, area and subject. Each individual fill action is recorded with the color and the exact elapsed time since the drawing appeared on screen. Researchers can also define expected results for each page and compare the data with their expectations. Tables can be exported to CSV for further processing in any spreadsheet or statistics software.

Researchers can compose their own surveys with custom images and sounds. The surveys are made available to test subjects through a fixed URL.


## How to deploy?

On the client side, test subjects just need to run a HTML5 capable browser.

On the server side, Coloring Book is a WSGI application, which means that it will run on any webserver that supports standard Python web applications. Apart from a WSGI-enabled webserver, install the dependencies using `pip install -r requirements.txt` or preferably `pip-sync` from the pip-tools package.

Assuming you opt to use MySQL (or anything other than SQLite), you need to create an empty database with pre-configured access rights for the Coloring Book application to use. For example by entering the following commands while running `mysql` as root user:

    create database coloringbook;
    grant all privileges on coloringbook.* to 'coloringbook'@'localhost' identified by 'myawesomepassword';

**Note** that you should not use the password quoted above. You can choose the name of the database and the name of the user freely as well.

Coloring Book obtains the necessary information to connect to the database from a user-provided configuration file. This is what the file contents should minimally look like:

    SQLALCHEMY_DATABASE_URI = 'mysql://coloringbook:myawesomepassword@localhost/coloringbook'
    SECRET_KEY = '12345678901234567890'

This file should be saved with a `.py` extension. Your WSGI startup module should pass the absolute path to this file as the first argument to `coloringbook.create_app`.

Before running the application, you need to run the database migrations. Use the following command:

    python manage.py -A -c CONFIG db upgrade

where `CONFIG` is the path to your local configuration file, either relative to the `coloringbook` package or absolute. Replace the last part of the command by `db -?` to get a summary of possible database manipulations.

The application does not take care of authentication or authorization. You should configure this directly on the webserver by restricting access to `/admin/`, for example using LDAP.

For development, you may run a local test server by invoking

    python manage.py -c CONFIG runserver -dr

The `-dr` flags switch on debugging settings and autoreloading. The application will run on `localhost:5000` by default, but you can change this by passing appropriate flags to the command. See the `-?` flag for details.


## Development

An overview of the database layout is given in `Database.svg`. For the complete specification, refer to `coloringbook/models.py`. Anything in `admin` subfolders is specific to the admin interface. Everything else in the `coloringbook` package is involved in delivering surveys to subjects and receiving data from them. Run `python test.py` for doctest-based testing. Motivations are documented throughout the code in comments; with some referencing to documentation for Flask, SQLAlchemy and jQuery, you should be able to find your way.


## Supporting users as a maintainer

As of the upcoming release, there are a few enhancements to the way subject data are submitted to and stored on the server. While this is an improvement overall, it does introduce two new ways in which you as a maintainer may be confronted with user problems.


### The exclamation mark

The first new category is that users may report that "an exclamation mark appeared next to the cogwheel", "there were errors" and/or they were told to "contact the maintainer". Users will do this because this is the information they get from the application front-end as well as from the manual in the admin panel. It means that data were successfully transmitted to the server, but they were not stored in the database because some of the data were invalid. Users are no longer required to attach the raw data when they report this type of problem to you, because the rejected data are written to the server application log together with a backtrace.

In order to handle this problem, use the date of the user report as a starting point and search backwards in time through the application log until you find the rejected data. Use the backtrace to determine the exact problem. If the problem is in the results data, previous log entries will tell you the exact enumeration order (starting from zero) of the page and the action that were affected. Correct the data, then see the next section for instructions on inserting the data into the database.

Note that multiple subjects may have been rejected when your user reports the exclamation mark. The application frontend does not distinguish between a single rejection and multiple rejections. Therefore, it is your responsibility to read backwards far enough to ensure that you find all rejected data that have not been dealt with yet.


### The red cogwheel

The second new category is that users may report that "the cogwheel did not turn blue", "the cogwheel stayed red", "the application was waiting for a connection" or "the application could not connect". This means either that data could not be transmitted to the server at all, or that the data were transmitted but the server did not confirm the transmission. When users report this, they should attach a large blob of plaintext data. Users are told that this blob is called the "buffer". The buffer consists of a timestamp, representing the date of the upload attempt, a URL, representing the survey to which the data belong, and a JSON array containing the data of one or more subjects.

When handling this problem, make sure that the subject data in the buffer really were not saved to the database by the server; otherwise, you might be duplicating data. You should also check the application log for any data invalidation that may have been logged without the user being notified. Once you have performed these checks, you can enter the data into the database as described in the next section.

Depending on the connectivity between the application frontend and the application server, subject data will be uploaded in one or more batches. For this reason, the buffer attached to a red cogwheel report may not include the data from all subjects in the session but only those included in the last batch. Previous upload batches may have been transmitted successfully. In fact, previous batches may have had invalid data, so a user may be reporting both the exclamation mark and the red cogwheel problem at the same time. Pay attention to what your user is telling you.


## Manually entering subject data into the database

You can enter data into the database both through the frontend and the backend. In the first case, you visit the survey URL with your browser and use the developer console to push subject data in batch mode to the server, in a JSON *array*. In the second case, you use the Flask shell on the server to enter subject data one subject at a time, in a JSON *object*.


### The frontend route

There are two ways in which you may determine the survey URL. If your user reported a red cogwheel, the second line of the attached buffer is the survey URL. If you took the data to be entered from the application log on the server, the log entry contains the name of the survey. In the latter case, concatenate the hostname, the `APPLICATION_ROOT` (most likely `/`), `/book/` and the survey name to find the survey URL.

Load the survey URL and wait for the registration form submit button to appear. Open the development console. Copypaste and parse your plaintext data in order to obtain native JavaScript objects. If the data are in an array already, assign this array directly to `transferFsm.buffer`.

    transferFsm.buffer = JSON.parse('[...]');

Otherwise, push the objects to this buffer one by one.

    transferFsm.buffer.push(JSON.parse('{...}'));

Finally, trigger an upload attempt and provide yourself with the diagnostics that users see when they use the application.

    transferFsm.handle('push');
    $('#starting_form').hide();
    $('#finish_controls, #status_details').show();


### The backend route

Log in to the server and activate the virtual environment of the application. Open the application shell with the following command:

    python manage.py -c /absolute/path/to/config.py shell

Inside the application shell, do some preparations. If you are working from a survey URL, the survey name is the last part of the pathname.

    from flask import json
    from coloringbook.views import store_subject_data
    from coloringbook.models import Survey
    survey = Survey.query.filter_by(name='survey-name').one()

Finally, enter the subject data one by one.

    store_subject_data(survey, json.loads('{...}'))
