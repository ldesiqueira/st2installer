import tempfile
import subprocess
import six
from six.moves import shlex_quote
from six.moves.urllib import parse as urlparse
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

    skip_key_check = self._get_query_param_value(request=request, param_name='skip_key_check',
                                                 param_type='bool', default_value=False)

    if skip_key_check:
        return 0
    else:
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

  def _parse_query_params(self, request):
    """
    Parse query string for the provided request.

    :rtype: ``dict``
    """
    query_string = request.query_string
    query_params = dict(urlparse.parse_qsl(query_string))

    return query_params

  def _get_query_param_value(self, request, param_name, param_type, default_value=None):
    """
    Return a value for the provided query param and optionally cast it for boolean types.

    If the requested query parameter is not provided, default value is returned instead.

    :param request: Request object.

    :param param_name: Name of the param to retrieve the value for.
    :type param_name: ``str``

    :param param_type: Type of the query param (e.g. "bool").
    :type param_type: ``str``

    :param default_value: Value to return if query param is not provided.
    :type default_value: ``object``
    """
    query_params = self._parse_query_params(request=request)
    value = query_params.get(param_name, default_value)

    if param_type == 'bool' and isinstance(value, six.string_types):
      value = value.lower() in ['1', 'true']

    return value
