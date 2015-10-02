import tempfile
import subprocess
import six
from six.moves import shlex_quote
from six.moves.urllib import parse as urlparse
from pecan import expose, request, response, redirect, abort
import random, string, os
from pecan import expose, request, response, abort
from Crypto.PublicKey import RSA
import os
from st2installer.controllers.base import BaseController


PARENT = os.path.dirname
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../'))

DEFAULT_RSA_KEY_SIZE = 2048


class KeypairController(BaseController):

    def __init__(self):
        _, self.privatefile = tempfile.mkstemp(suffix='private')
        _, self.publicfile = tempfile.mkstemp(suffix='public')

        self.diff_output = '/tmp/keycompare.log'
        self.ssh_diff = os.path.join(ROOT_DIR, 'keycompare')
        self.ssl_diff = os.path.join(ROOT_DIR, 'sslcompare')

        self.gen_private = RSA.generate(DEFAULT_RSA_KEY_SIZE, os.urandom)
        self.gen_public = self.gen_private.publickey()

    def compare(self, diff, private, public):
        with open(self.privatefile, 'w') as temp_private:
            temp_private.write(private)
        with open(self.publicfile, 'w') as temp_public:
            temp_public.write(public)

        args = [diff, self.privatefile, self.publicfile]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout

    @expose(generic=True, content_type='text/plain')
    def index(self):
        abort(400)

    @index.when(method='POST')
    def index_post(self):
        if request.POST['comparison'] == 'ssh':
            private_field = 'file-ssh-privatekey'
            public_field = 'file-ssh-publickey'
            diff = self.ssh_diff
        else:
            private_field = 'file-privatekey'
            public_field = 'file-publickey'
            diff = self.ssl_diff

        private = request.POST[private_field]
        public = request.POST[public_field]

        skip_key_check = self._get_query_param_value(request=request,
                                                     param_name='skip_key_check',
                                                     param_type='bool',
                                                     default_value=False)

        if skip_key_check:
            return 0
        else:
            return self.compare(diff, private.file.read(),
                                public.file.read())

    @expose('json')
    def keygen(self):
        return {
            'private': self.gen_private.exportKey('PEM'),
            'public': self.gen_public.exportKey('OpenSSH')[8:]
        }

    @expose(content_type='application/octet-stream')
    def private(self):
        response.headers['Content-Disposition'] = 'attachment; filename="st2-ssh.key"'
        return self.gen_private.exportKey('PEM')

    @expose(content_type='application/octet-stream')
    def public(self):
        response.headers['Content-Disposition'] = 'attachment; filename="st2-ssh.pub"'
        return self.gen_public.exportKey('OpenSSH')
