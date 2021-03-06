#!/usr/bin/env python3

# Original Author: Peter Bui
# Modified by Catalina Vajiac and Noah Yoshida

import collections
import glob
import hashlib
import logging
import os
import random
import socket
import pymysql
import string
import subprocess
import sys
import magic
import time

import tornado.ioloop
import tornado.options
import tornado.web

import pygments
import pygments.lexers
import pygments.formatters
import pygments.styles
import pygments.util

from secrets import DATABASE_CREDS
from google.cloud import storage
from google.auth import compute_engine

# Configuration ----------------------------------------------------------------

YLDME_PRESETS   = [
    ('url'              , 'http://yld.me', 'url'),
    ('paste'            , 'http://yld.me', 'url'),
    ('pbui'             , 'http://www3.nd.edu/~pbui', 'url'),
    ('cdt-30010-fa15'   , 'https://www3.nd.edu/~pbui/teaching/cdt.30010.fa15/', 'url'),
    ('cdt-30020-sp16'   , 'https://www3.nd.edu/~pbui/teaching/cdt.30020.sp16/', 'url'),
    ('cse-20189-sp16'   , 'https://www3.nd.edu/~pbui/teaching/cse.20189.sp16/', 'url'),
    ('cse-40175-sp16'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.sp16/', 'url'),
    ('cdt-30010-fa16'   , 'https://www3.nd.edu/~pbui/teaching/cdt.30010.fa16/', 'url'),
    ('cse-30331-fa16'   , 'https://www3.nd.edu/~pbui/teaching/cse.30331.fa16/', 'url'),
    ('cse-40175-fa16'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.fa16/', 'url'),
    ('cse-40175-sp17'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.sp17/', 'url'),
    ('cse-40842-sp17'   , 'https://www3.nd.edu/~pbui/teaching/cse.40842.sp17/', 'url'),
    ('cse-20289-sp17'   , 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp17/', 'url'),
    ('cse-30341-fa17'   , 'https://www3.nd.edu/~pbui/teaching/cse.30341.fa17/', 'url'),
    ('cse-30872-fa17'   , 'https://www3.nd.edu/~pbui/teaching/cse.30872.fa17/', 'url'),
    ('cse-40175-fa17'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.fa17/', 'url'),
    ('cse-20289-sp18'   , 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp18/', 'url'),
    ('cse-40175-sp18'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.sp18/', 'url'),
    ('cse-40850-sp18'   , 'https://www3.nd.edu/~pbui/teaching/cse.40850.sp18/', 'url'),
    ('eg-44175-su18'    , 'https://www3.nd.edu/~pbui/teaching/eg.44175.su18/' , 'url'),
    ('cse-30341-fa18'   , 'https://www3.nd.edu/~pbui/teaching/cse.30341.fa18/', 'url'),
    ('cse-30872-fa18'   , 'https://www3.nd.edu/~pbui/teaching/cse.30872.fa18/', 'url'),
    ('cse-40175-fa18'   , 'https://www3.nd.edu/~pbui/teaching/cse.40175.fa18/', 'url'),
    ('pbc-su17'         , 'https://www3.nd.edu/~pbui/teaching/pbc.su17/'      , 'url'),
]

YLDME_URL       = 'http://yld.us'
YLDME_PORT      = 5000
YLDME_ADDRESS   = '0.0.0.0'
YLDME_ALPHABET  = string.ascii_letters + string.digits
YLDME_MAX_TRIES = 10
YLDME_ASSETS    = os.path.join(os.path.dirname(__file__), 'assets')
YLDME_STYLES    = os.path.join(YLDME_ASSETS, 'css', 'pygments')

# Constants --------------------------------------------------------------------

TRUE_STRINGS = ('1', 'true', 'on', 'yes')

# Utilities --------------------------------------------------------------------

def upload_blob(source, destination_blob_name, bucket_name="yldme-storage"):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(source)

def download_blob(destination_blob_name, bucket_name="yldme-storage"):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    data = blob.download_as_string()
    return data

def integer_to_identifier(integer, alphabet=YLDME_ALPHABET):
    ''' Returns a string given an integer identifier '''
    identifier = ''
    number     = int(integer)
    length     = len(alphabet)

    while number >= length:
        quotient, remainder = divmod(number, length)
        identifier = alphabet[remainder] + identifier
        number     = quotient - 1

    identifier = alphabet[number] + identifier
    return identifier

def checksum(data):
    return hashlib.sha1(data).hexdigest()

def determine_mimetype(blob):
    return magic.from_buffer(blob, mime=True)

# Database ---------------------------------------------------------------------

YldMeTupleFields = 'id ctime mtime hits type name value'.split()
YldMeTuple       = collections.namedtuple('YldMeTuple', YldMeTupleFields)

def parse_db_row(row):
    if row != None and len(row) == len(YldMeTupleFields):
        return YldMeTuple(*row)
    else:
        return row

class Database(object):

    SQL_CREATE_TABLE = '''
    CREATE TABLE IF NOT EXISTS YldMe (
        id      INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
        ctime   INT NOT NULL,
        mtime   INT NOT NULL,
        hits    INT NOT NULL DEFAULT 0,
        type    varchar(255) NOT NULL DEFAULT 'url',
        name    varchar(255) NOT NULL UNIQUE,
        value   varchar(255) NOT NULL UNIQUE,
        CONSTRAINT chk_type CHECK (type='url' OR type='paste')
    );
    '''
    SQL_INSERT_DATA   = "INSERT INTO YldMe (ctime, mtime, type, name, value) VALUES ({}, {}, '{}', '{}', '{}')"
    SQL_UPDATE_DATA   = 'UPDATE YldMe SET hits={},mtime={} WHERE id={}'
    SQL_SELECT_NAME   = "SELECT * FROM YldMe WHERE name='{}'"
    SQL_SELECT_VALUE  = "SELECT * FROM YldMe WHERE value='{}'"
    SQL_SELECT_COUNT  = 'SELECT COUNT(*) FROM YldMe;'

    def __init__(self, path=None):
        self.conn = pymysql.connect(*DATABASE_CREDS)

        with self.conn:
            curs = self.conn.cursor()
            curs.execute(Database.SQL_CREATE_TABLE)

        for name, value, type in YLDME_PRESETS:
            try:
                self.add(name, value, type)
            except:
                pass

    def add(self, name, value, type=None):
        type = type or 'url'
        with self.conn:
            data = (
                int(time.time()),
                int(time.time()),
                type,
                name,
                value,
            )
            curs = self.conn.cursor()
            curs.execute(Database.SQL_INSERT_DATA.format(*data))

    def get(self, name):
        with self.conn:
            curs = self.conn.cursor()
            curs.execute(Database.SQL_SELECT_NAME.format(name))
            return parse_db_row(curs.fetchone())

    def hit(self, name):
        data = self.get(name)
        with self.conn:
            curs = self.conn.cursor()
            curs.execute(Database.SQL_UPDATE_DATA.format(data.hits + 1, int(time.time()), data.id))

    def lookup(self, value):
        with self.conn:
            curs = self.conn.cursor()
            curs.execute(Database.SQL_SELECT_VALUE.format(value))
            return parse_db_row(curs.fetchone())

    def count(self):
        with self.conn:
            curs = self.conn.cursor()
            curs.execute(Database.SQL_SELECT_COUNT)
            return  int(curs.fetchone()[0]) + 1

# Handlers ---------------------------------------------------------------------

class YldMeHandler(tornado.web.RequestHandler):

    def get(self, name=None):
        if name is None:
            return self._index()

        data = self.application.database.get(name)
        if data is None:
            return self._index()

        self.application.database.hit(name)

        if data.type == 'url':
            self._get_url(name, data)
        else:
            self._get_paste(name, data)

    def _get_url(self, name, data):
        self.redirect(data.value)

    def _get_paste(self, name, data):
        file_data = download_blob(name)
        file_mime = determine_mimetype(file_data)

        if self.get_argument('raw', '').lower() in TRUE_STRINGS:
            self.set_header('Content-Type', file_mime)
            self.write(file_data)
            return

        style   = self.get_argument('style', 'default')
        linenos = self.get_argument('linenos', False)

        if 'text/' in file_mime or 'message/' in file_mime:
            try:
                lexer = pygments.lexers.guess_lexer(file_data.decode('utf8'))
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.get_lexer_for_mimetype('text/plain')

            formatter = pygments.formatters.HtmlFormatter(cssclass='hll', linenos=linenos, style=style)
            file_html = pygments.highlight(file_data, lexer, formatter)
        elif 'image/' in file_mime:
            file_html = '<div class="thumbnail"><img src="/{}?raw=1" class="img-responsive"></div>'.format(name)
        else:
            file_html = '''
<div class="btn-toolbar" style="text-align: center">
    <a href="/{}?raw=1" class="btn btn-primary"><i class="fa fa-download"></i> Download</a>
</div>
'''.format(name)

        self.render('paste.tmpl', **{
            'name'      : name,
            'file_html' : file_html,
            'pygment'   : style,
            'styles'    : self.application.styles,
        })

    def _index(self):
        self.render('index.tmpl')

    def post(self, type=None):
        value = self.request.body
        if type == 'url':
            value_hash = value
        elif type == 'paste':
            value_hash = checksum(value)
        elif type == 'metrics':
            self.write('metric check')
            return None
        else:
            raise tornado.web.HTTPError(405, 'Could not post to {}'.format(type))
        data  = self.application.database.lookup(value_hash)
        tries = 0

        while data is None and tries < YLDME_MAX_TRIES:
            tries = tries + 1

            try:
                name = self.application.generate_name()
                self.application.database.add(name, value_hash, type)
                if type != 'url':
                    upload_blob(value, name)
                data = self.application.database.get(name)
            except Exception as e:
                print('adding failed')
                self.application.logger.warn(e)
                continue

        if tries >= YLDME_MAX_TRIES:
            raise tornado.web.HTTPError(500, 'Could not produce new database entry')

        self.write('{}/{}\n'.format(YLDME_URL, data.name))

class YldMeRawHandler(tornado.web.RequestHandler):
    def get(self, name=None):
        self.redirect('/{}?raw=1'.format(name or ''))

# Application ------------------------------------------------------------------

class YldMeApplication(tornado.web.Application):

    def __init__(self, **settings):
        tornado.web.Application.__init__(self, **settings)

        self.logger   = logging.getLogger()
        self.address  = settings.get('address', YLDME_ADDRESS)
        self.port     = settings.get('port', YLDME_PORT)
        self.ioloop   = tornado.ioloop.IOLoop.instance()
        self.database = Database()
        self.styles   = [os.path.basename(path)[:-4] for path in sorted(glob.glob(os.path.join(YLDME_STYLES, '*.css')))]

        self.add_handlers('.*', [
                (r'.*/assets/(.*)', tornado.web.StaticFileHandler, {'path': YLDME_ASSETS}),
                (r'.*/raw/(.*)'   , YldMeRawHandler),
                (r'.*/(.*)'       , YldMeHandler),
        ])

    def generate_name(self):
        return integer_to_identifier(random.randrange(self.database.count()*10))

    def run(self):
        try:
            self.listen(self.port, self.address)
        except socket.error as e:
            self.logger.fatal('Unable to listen on {}:{} = {}'.format(self.address, self.port, e))
            sys.exit(1)

        self.ioloop.start()

# Main execution ---------------------------------------------------------------

if __name__ == '__main__':
    tornado.options.define('debug', default=False, help='Enable debugging mode.')
    tornado.options.define('port', default=YLDME_PORT, help='Port to listen on.')
    tornado.options.define('template_path', default=os.path.join(os.path.dirname(__file__), "templates"), help='Path to templates')
    tornado.options.parse_command_line()

    options = tornado.options.options.as_dict()
    yldme   = YldMeApplication(**options)
    yldme.run()

# vim: sts=4 sw=4 ts=8 expandtab ft=python
