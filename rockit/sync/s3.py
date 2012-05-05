"""Utilities for working with Amazon S3 file storage."""

import boto
from boto.s3.key import Key
from boto.exception import S3ResponseError
import os
import time

from django.conf import settings


def _printer(msg):
    print msg


class _Log:
    def __getattr__(self, name):
        return _printer

log = _Log()


default_retry_sleep_time = 2.0


class S3KeyExists(Exception):
    """A key in the specified bucket already exists."""


def get_connection(**kwargs):
    access_key = settings.S3_ACCESS_ID
    if not access_key:
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        if not access_key:
            raise EnvironmentError(
                "Missing config value for 'aws_access_key_id' "
                "or environment variable AWS_ACCESS_KEY_ID")

    secret_key = settings.S3_SECRET_KEY
    if not secret_key:
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if not secret_key:
            raise EnvironmentError(
                "Missing config value for 'aws_secret_access_key' or "
                "environment variable AWS_SECRET_ACCESS_KEY")

    kwargs['aws_access_key_id'] = access_key
    kwargs['aws_secret_access_key'] = secret_key
    conn = boto.connect_s3(**kwargs)
    return conn


def run_in_retry_loop(fn, max_retries=4,
                      retry_sleep_time=default_retry_sleep_time):
    success = False
    retry = 0
    while not success:
        try:
            result = fn()
        except S3ResponseError:
            success = False
            retry += 1
            if retry >= max_retries:
                log.warning("Too many retries (%s)" % max_retries)
                raise
            time.sleep(retry_sleep_time)
            fn_name = getattr(fn, '__name__', repr(fn))
            log.exception("** RETRYING %s after exception:" % fn_name)
        else:
            success = True
    return result


def get_key(key_path):
    conn = get_connection()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    return Key(bucket, name=key_path)


def get_key_contents(key_path):
    key = get_key(key_path)
    return run_in_retry_loop(key.get_contents_as_string)


def move_local_file_into_s3_dir(local_file, s3_path, make_public=True,
                                retry_sleep_time=default_retry_sleep_time,
                                make_protected=False,
                                basename=None, headers={},
                                unlink_source=True):
    conn = get_connection()
    bucket = conn.get_bucket(settings.S3_BUCKET)
    key_name = s3_path
    k = Key(bucket, name=key_name)
    if k.exists():
        log.warning("** already exists: %r, deleting: %r"
                    % (key_name, local_file))
        return

    def set_contents():
        k.set_contents_from_filename(local_file, headers=headers)
    run_in_retry_loop(set_contents, retry_sleep_time=retry_sleep_time)

    if unlink_source:
        os.unlink(local_file)
    if make_public:
        assert not make_protected, 'cannot mix make_public and make_protected'
        run_in_retry_loop(k.make_public, retry_sleep_time=retry_sleep_time)
    elif make_protected:
        mp = lambda: bucket.set_canned_acl('authenticated-read', key_name)
        run_in_retry_loop(mp, retry_sleep_time=retry_sleep_time)

    log.info('uploaded %s' % key_name)


def get_authenticated_url(key, expires_in=60 * 30,  # 30 min
                          bucket=settings.S3_BUCKET,
                          method='GET'):
    conn = get_connection()
    return conn.generate_url(expires_in, method, bucket=bucket, key=key,
                             query_auth=True)
