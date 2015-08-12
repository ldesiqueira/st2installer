from pecan import expose, request, response, redirect, abort
from subprocess import call
import random, string, os
from Crypto.PublicKey import RSA

class KeypairController(object):

  private = '/tmp/testkey'
  public = '/tmp/testkey-pub'
  diff_output = '/tmp/keycompare.log'
  ssh_diff = '/etc/st2installer/keycompare'
  ssl_diff = '/etc/st2installer/sslcompare'
  gen_private = RSA.generate(1024, os.urandom)
  gen_public = gen_private.publickey()

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
    with open(self.private, 'w') as temp_private:
      temp_private.write(upload_private.file.read())
    with open(self.public, 'w') as temp_public:
      temp_public.write(upload_public.file.read())
    call("%s > %s" % (diff, self.diff_output), shell=True)
    with open(self.diff_output, 'r') as output:
      data = output.read()
    return data

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
  