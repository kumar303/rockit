rockit
======

Server component to [Herbie](https://github.com/ednapiranha/herbie),
an html5 audio player.

Python 2.6 or higher, MySQL, and some command line tools are required.

Clone the code recursively:

    git clone --recursive git://github.com/kumar303/rockit.git

Make a virtualenv then install the compiled modules:

    cd rockit
    pip install -r requirements/compiled.txt

Install mpg123 and oggenc command line tools.
On Mac with homebrew, you could type:

    brew install mpg123 vorbis-tools

Get your mysql database set up:

    mysql -u root -e 'create database rockit'

Copy over the settings file:

    cp rockit/settings/local.py-dist rockit/settings/local.py

Sync it up!

    python manage.py syncdb --noinput

Here are some things to set in your local settings:

- ``S3_ACCESS_ID``, your Amazon S3 access ID
- ``S3_SECRET_KEY``, your Amazon S3 secret key
- ``S3_BUCKET``, a unique bucket name on S3
- ``LAST_FM_KEY``, your Last.fm API key if you want album art

Start the server:

    python manage.py runserver

You can now run a server to synchronize mp3s with Amazon S3.
To actually upload mp3 files, use [rocketlib](https://github.com/kumar303/rockitlib)

playdoh
=======

Mozilla's Playdoh is a web application template based on [Django][django].

Patches are welcome! Feel free to fork and contribute to this project on
[github][gh-playdoh].

Full [documentation][docs] is available as well.


[django]: http://www.djangoproject.com/
[gh-playdoh]: https://github.com/mozilla/playdoh
[docs]: http://playdoh.rtfd.org/


License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://creativecommons.org/licenses/BSD/

