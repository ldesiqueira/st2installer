from pecan import expose, request, response, abort
from subprocess import call
from Crypto.PublicKey import RSA
import os


class KeypairController(object):

    def __init__(self):
        parent = os.path.dirname
        rootdir = parent(parent(parent(os.path.realpath(__file__))))

        self.privatefile = '/tmp/testkey'
        self.publicfile = '/tmp/testkey-pub'
        self.diff_output = '/tmp/keycompare.log'

        self.ssh_diff = '%s/keycompare' % rootdir
        self.ssl_diff = '%s/sslcompare' % rootdir
        self.gen_private = RSA.generate(1024, os.urandom)
        self.gen_public = self.gen_private.publickey()

    def compare(self, diff, private, public):
        with open(self.privatefile, 'w') as temp_private:
            temp_private.write(private)
        with open(self.publicfile, 'w') as temp_public:
            temp_public.write(public)
        call("%s > %s" % (diff, self.diff_output), shell=True)
        with open(self.diff_output, 'r') as output:
            return output.read()

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
        return self.compare(diff, private.file.read(), public.file.read())

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

