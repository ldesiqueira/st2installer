import tempfile
import subprocess
from six.moves import shlex_quote
from pecan import expose, request, response, redirect, abort
import random, string, os
from Crypto.PublicKey import RSA

DEFAULT_RSA_KEY_SIZE = 2048

class KeypairController(object):

  def __init__(self):
    _, self.privatefile = tempfile.mkstemp(suffix='private')
    _, self.publicfile = tempfile.mkstemp(suffix='public')
    self.diff_output = '/tmp/keycompare.log'
    self.ssh_diff = '/etc/st2installer/keycompare'
    self.ssl_diff = '/etc/st2installer/sslcompare'
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
    upload_private = request.POST[private_field]
    upload_public = request.POST[public_field]
    return self.compare(diff, upload_private.file.read(), upload_public.file.read())

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
