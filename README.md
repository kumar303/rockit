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

Install ffmpeg to do transcoding.
On Mac with homebrew, you could type:

    brew install ffmpeg

You also need the ffprobe command line tool but hopefully the ffmpeg package
also installed that.

Get your mysql database set up:

    mysql -u root -e 'create database rockit'

Build the database schema:

    ./vendor/src/schematic/schematic migrations

Copy over the settings file:

    cp rockit/settings/local.py-dist rockit/settings/local.py

Here are some things to set in your local settings:

- ``S3_ACCESS_ID``, your Amazon S3 access ID
- ``S3_SECRET_KEY``, your Amazon S3 secret key
- ``S3_BUCKET``, a unique bucket name on S3
- ``LAST_FM_KEY``, your Last.fm API key if you want album art

Start the server:

    python manage.py runserver

You can now run a server to synchronize mp3s with Amazon S3.

uploads
=======

To upload mp3 files, use [rocketlib](https://github.com/kumar303/rockitlib)

You have to grant each user an upload key for that to work though.
Run this command to make one:

    python manage.py uploadkey --email user@somewhere.com

creating a UI
=============

rockit is a service/API that you can interact with over JSON.
You need to be a registered UI client so that you can talk to the API.
This means you need an API key and you have to sign all your requests with that
key. We use [JWT](http://openid.net/specs/draft-jones-json-web-token-07.html)
(JSON Web Tokens) to make this happen.

As a rockit server administrator, edit your ``rockit/settings/local.py`` file
and add an API client like this:

    API_CLIENTS = {'awesome.ui': '<a secret key>'}

Now, ``awesome.ui`` is authorized to make API requests. Here's how the UI admin
would sign a request to view all music for Browser ID user ``edna@wat.com``:

    import jwt
    import urllib2
    req = {'iss': 'awesome.ui',
           'aud': 'http://localhost:8000',
           'request': {'email': 'edna@wat.com'}}
    signed_req = jwt.encode(req, '<a secret key>')
    fp = urllib2.urlopen('http://localhost:8000/music/?r=%s' % signed_req)
    response = fp.read()


The **iss** is the issuer, in other words the registered key in API_CLIENTS.
The **aud** is the audience, in this case the domain of the API.
The ``request`` dictionary is specific to the ``/music/`` URL. Other URLs
might expect different requests. The signed request is always passed
through a GET or POST var (depending on what the operation is)
named ``r``. This code example is in Python using
[PyJWT](https://github.com/progrium/pyjwt) but there are many
JWT libraries to choose from in your language of choice.

API
===

**GET /music/?r=_signedRequest_**

Gets all tracks for user by email.

Example request:

    {'iss': 'awesome.ui',
     'aud': 'http://localhost:8000',
     'request': {'email': 'edna@wat.com',
                 'page_size': 100,
                 'offset': 0}}

Example response:

    {'tracks': [{'s3_urls': {'ogg': '<s3 url>',
                             'mp3': '<s3 url>'},
                 'id': 12345,
                 'artist': 'Gescom',
                 'track': 'Horse',
                 'album': u'Minidisc',
                 'album_art_url': '<lastfm url>',
                 'medium_art_url': '<lastfm url>',
                 'small_art_url': '<lastfm url>',
                 'large_art_url': '<lastfm url>'}]}


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

