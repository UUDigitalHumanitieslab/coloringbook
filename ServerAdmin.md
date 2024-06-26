# Coloring Book Server Administration

## Supporting users as a maintainer

As of release 2.0, there are a few enhancements to the way subject data are submitted to and stored on the server. While this is an improvement overall, it does introduce two new ways in which you as a maintainer may be confronted with user problems.


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
