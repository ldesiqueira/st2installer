from pecan import expose, request, Response, redirect, abort
from subprocess import call
import random, string, os
from Crypto.PublicKey import RSA

class KeypairController(object):

  private = '/tmp/testkey'
  public = '/tmp/testkey-pub'
  diff = '/usr/bin/keycompare'
  diff_output = '/tmp/keycompare.log'

  @expose(generic=True, content_type='text/plain')
  def index(self):
    abort(400)

  @index.when(method='POST')
  def index_post(self):
    if request.POST['comparison'] == 'ssh':
      private_field = 'file-ssh-privatekey'
      public_field = 'file-ssh-publickey'
    else:
      private_field = 'file-privatekey'
      public_field = 'file-publickey'
    upload_private = request.POST[private_field]
    upload_public = request.POST[public_field]
    with open(self.private, 'w') as temp_private:
      temp_private.write(upload_private.file.read())
    with open(self.public, 'w') as temp_public:
      temp_public.write(upload_public.file.read())
    call("%s > %s" % (self.diff, self.diff_output), shell=True)
    with open(self.diff_output, 'r') as output:
      data = output.read()
    return data

  @expose('json')
  def keygen(self):
    private = RSA.generate(1024, os.urandom)
    return {
      'private': private.exportKey('PEM'),
      'public': private.publickey().exportKey('OpenSSH')
    }