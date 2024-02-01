# Coloring Book

A web-based coloring book survey application
by the Research Software Lab of the Centre for Digital Humanities at Utrecht University

**Project website:** https://coloringbook.hum.uu.nl/

**Research paper:** Pinto, M., & Zuckerman, S. (2019). Coloring Book: A new method for testing language comprehension. _Behavior research methods_, _51_(6), 2609-2628.

**Contact information:** coloringbook@uu.nl

**IP and license:** The intellectual property of the ColoringBook method belongs to Utrecht University. This software is intended for research purposes. For the license details see below.


## Why does it exist?

The software allows researchers to test how subjects interpret language (words and sentences), in a playful manner without revealing the intent of the study. Moreover, it is a natural task for subjects that doesn't make them *feel* like they are being tested. It is designed to work well on tablet devices, in order to accomodate for very young subjects.


## What does it do?

Test subjects are presented with a subscription form, instructions, a series of coloring pages and finally an evaluation form. After both forms have been completed and all pages have been colored, all data are submitted to the server at once.

Each coloring page is presented with a coloring instruction sentence (as a written text, sound or both), for example "the blue monkey is jumping". The instruction sentence can appear simultaneously with the coloring page, or before it. The subject is given the means to pick colors and fill areas of the drawing by point-and-click. This also works on touch devices. All data for the coloring pages are downloaded to the client side at once before the survey starts.

On the server side, all coloring data are collected in a table that can be filtered by survey, page, area and subject. Each individual fill action is recorded with the color and the exact elapsed time since the drawing appeared on screen. Researchers can also define expected results for each page and compare the data with their expectations. Tables can be exported to CSV for further processing in any spreadsheet or statistics software.

Researchers can compose their own surveys with custom images and sounds. The surveys are made available to test subjects through a fixed URL.


## How do I deploy and run the application?

On the client side, test subjects just need to run a HTML5 capable browser.

Coloring Book is deployed using Docker Compose. It has two deployment modes: `prod` (for production deployment) and `dev` (for local development). There are two main differences between the two. First, `dev` mode will build a container with a MySQL database, while in `prod` mode, the host machine is expected to run a MariaDB that the app will use. Secondly, the containers log much more (debugging)information in `dev` mode than in `prod` mode. 

In either mode, the application needs two configuration files.

Docker needs a file called `.env` to be present in the same folder as `docker-compose.yml`, containing at least the following settings.

    CONFIG_FILE=abcdefg
    DB_HOST=abcdefg
    DB_PORT=1234
    DB_USER=abcdefg
    DB_PASSWORD=abcdefg
    DB_DB=abcdefg
    DB_ROOT_PASSWORD=abcdefg

`DB_HOST` should be set to `db-dev` if the application is run in `dev` mode. In `prod` mode, the settings should correspond to existing database and user settings on the host machine. The user must be configured to use the `mysql_native_password` authentication plugin. This is not the default in modern versions of MySQL or MariaDB

The setting `CONFIG_FILE` should be refer to the name of a configuration file (e.g. `CONFIG_FILE=config.py`). Create this file, put it in the `coloringbook` package folder and add at least the following settings.

    SQLALCHEMY_DATABASE_URI = 'mysql://coloringbook:myawesomepassword@dbhost/coloringbook'
    SECRET_KEY = '12345678901234567890'
    MAIL_SERVER = 'mail.server.com'
    MAIL_PORT = 1234
    MAIL_USE_TLS = True/False
    MAIL_USE_SSL = True/False
    MAIL_USERNAME = 'username'
    MAIL_PASSWORD = 'password'
    MAIL_DEFAULT_SENDER = 'mysender@email.address'

In development mode, the part of `SQLALCHEMY_DATABASE_URI` that specifies the host (`dbhost` in the example above) should be set to `db-dev`.

With both files present, run either `docker compose --profile dev up --build` (development mode) or `docker compose --profile prod up --build` (production mode) in the root directory of the project will start three or four containers, depending on the deployment mode.

| Name (`prod`) | Name (`dev`) | Description                              |
|---------------|--------------|------------------------------------------|
| `app`         | `app-dev`    | The Coloring book webserver proper       |
| (NA)          | `db-dev`     | A MySQL DB (only on `dev`)               |
| `redis`       | `redis`      | A Redis message broker                   |
| `worker`      | `worker-dev` | A Celery instance for asynchronous tasks |

Docker should automatically create the database (if it does not exist) and run the available migrations. To run migrations manually, run

    python manage.py -A -c CONFIG db upgrade

where `CONFIG` is the path to your local configuration file, either relative to the `coloringbook` package or absolute. Replace the last part of the command by `db -?` to get a summary of possible database manipulations.

The project source files are automatically mounted to the local file system. In development mode (see below), any changes made to the application are applied immediately, and the server is reloaded ('live reload').

The application does not take care of authentication or authorization. You should configure this directly on the webserver by restricting access to `/admin/`, for example using LDAP.

By default, the application will run on `localhost:5000`, but this is customisable in the `Dockerfile`.


## Development

An overview of the database layout is given in `Database.svg`. For the complete specification, refer to `coloringbook/models.py`. Anything in `admin` subfolders is specific to the admin interface. Everything else in the `coloringbook` package is involved in delivering surveys to subjects and receiving data from them. Run `python test.py` for doctest-based testing. Motivations are documented throughout the code in comments; with some referencing to documentation for Flask, SQLAlchemy and jQuery, you should be able to find your way.

It is possible to run the server in the development mode by adding the following line to `.env`. 

```
DEVELOPMENT=1
``` 

This will print debug messages in the container logs and enable automatic reloading when the source files are changed.


## Server maintenance

Once deployed, you may need to support users and restore missing data. How to do this is described in detail in the adjacent [ServerAdmin.md](ServerAdmin.md).


## License

This software is intended for research purposes. Licensed under the EUPL-1.2 or later. See the adjacent [LICENSE](LICENSE) file for licensing details.
