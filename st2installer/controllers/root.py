from pecan import expose, request, Response, redirect, abort
from subprocess import Popen, PIPE, call
from keypair import KeypairController
from uuid import uuid1
import random, string, os, yaml

class RootController(object):

  proc = None
  command = '/usr/bin/sudo nocolor=1 /usr/bin/puprun'
  output = '/tmp/st2installer.log'
  keypair = KeypairController()
  path = "/opt/puppet/hieradata/"
  configname = "workroom.yaml"
  password_length = 32
  password_chars = string.ascii_letters + string.digits + '!@#$%^&*()'
  hostname = ""
  password = ""

  # Note, any command added here needs to be added to the workroom sudoers entry.
  # File can be found at https://github.com/StackStorm/st2workroom/blob/master/modules/profile/manifests/st2server.pp#L513
  cleanup_chain = [
    "/bin/rm %s%s" % (path, configname),
    "/usr/bin/sudo /usr/bin/st2 run st2.call_home",
    "/usr/bin/sudo /usr/bin/st2ctl reload --register-all",
    "/usr/bin/sudo /usr/sbin/service hubot restart",
  ]

  def lock(self):
    open('/tmp/st2installer_lock', 'w').close()
  def is_locked(self):
    return os.path.isfile('/tmp/st2installer_lock')

  @expose(content_type='text/plain')
  def cleanup(self):
    for command in self.cleanup_chain:
      Popen(command, shell=True)
    return "done"
 
  @expose(content_type='text/plain')
  def puppet(self, line):
    if not self.proc:
      open(self.output, 'w').close()
      self.proc = Popen("%s > %s 2>&1" % (self.command, self.output), shell=True)
      self.lock()

    data = ''
    logfile = open(self.output, 'r')
    for i, logline in enumerate(logfile):
      if i>=int(line):
        data += logline.strip()+'\n'
    logfile.close()

    if self.proc.poll() is not None:
      data += '--terminate--'

    if not data:
      return '--idle--'

    return data

  @expose(generic=True, template='index.html')
  def index(self):
    
    if self.is_locked():
      redirect('/install', internal=True)

    password = ''.join([random.choice(self.password_chars) for n in xrange(self.password_length)])

    return { "hubotpassword": password }

  @index.when(method='POST', template='progress.html')
  def index_post(self, **kwargs):

    if self.is_locked():
      redirect('/install', internal=True)

    password = kwargs['hubot-password']
    collect_anonymous_data = True if kwargs["anon-data"] else False
    uuid = str(uuid1())

    config = {
      "system::hostname":               kwargs['hostname'],
      "st2::installer_run":             True,
      "st2::api_url":                   "https://%s:9101" % kwargs['hostname'],
      "st2::auth_url":                  "https://%s:9100" % kwargs['hostname'],
      "st2::cli_api_url":               "https://%s:9101" % kwargs['hostname'],
      "st2::cli_auth_url":              "https://%s:9100" % kwargs['hostname'],
      "st2::stanley::username":         kwargs['username'],
      "users": {
        "admin": {
          "password": kwargs['password-1'],
          "admin": True,
        },
        "chatops_bot": {
          "password": password,
          "shell": "/bin/false"
        }
      },
      "groups": {
        "robots": {
          "gid": "6000",
        }
      },
      "st2::kvs": {
        "st2::server_uuid": {
          "value": uuid,
        },
        "st2::collect_anonymous_data": {
          "value": collect_anonymous_data
        },
        "st2::user_data": {
          "value": "{}"
        }
      }
    }

    if kwargs["selfsigned"] == "0":
      config["st2::ssl_public_key"] = request.POST['file-publickey'].file.read()
      config["st2::ssl_private_key"] = request.POST['file-privatekey'].file.read()

    if kwargs["sshgen"] == "0":
      config["st2::ssh_public_key"] = request.POST['file-publickey'].file.read()
      config["st2::ssh_private_key"] = request.POST['file-privatekey'].file.read()
    else:
      config["st2::stanley::ssh_private_key"] = kwargs['gen-private']
      config["st2::stanley::ssh_public_key"] = kwargs['gen-public']

    if kwargs["check-chatops"] == "1":

      config.update({
        "hubot::chat_alias": "!",
        "hubot::env_export": {
          "HUBOT_LOG_LEVEL":   "debug",
          "ST2_AUTH_USERNAME": "chatops_bot",
          "ST2_AUTH_PASSWORD": password,
          "ST2_API": "https://%s:9101" % kwargs['hostname'],
          "ST2_WEBUI_URL": "https://%s" % kwargs['hostname'],
          "ST2_AUTH_URL": "https://%s:9100" % kwargs['hostname'],
          "NODE_TLS_REJECT_UNAUTHORIZED": "0"
        },
        "hubot::external_scripts": ["hubot-stackstorm"],
        "hubot::dependencies": {
          "hubot": ">= 2.6.0 < 3.0.0",
          "hubot-scripts": ">= 2.5.0 < 3.0.0",
          "hubot-stackstorm": ">= 0.2.2 < 0.3.0"
        },
      })

      if kwargs["chatops"] == "example":
        config["hubot::adapter"] = "irc"
        config["hubot::env_export"].update({
          "HUBOT_IRC_SERVER":   "localhost",
          "HUBOT_IRC_ROOMS":    "#stackstorm",
          "HUBOT_IRC_NICK":     kwargs['username'],
          "HUBOT_IRC_UNFLOOD":  True
        })
        config["hubot::dependencies"]["hubot-irc"] = ">=0.2.7 < 1.0.0"
      elif kwargs["chatops"] == "irc":
        config["hubot::adapter"] = "irc"
        config["hubot::env_export"].update({
          "HUBOT_IRC_SERVER":   kwargs["irc-server"],
          "HUBOT_IRC_ROOMS":    kwargs["irc-rooms"],
          "HUBOT_IRC_NICK":     kwargs['username'],
          "HUBOT_IRC_UNFLOOD":  True
        })
        config["hubot::dependencies"]["hubot-irc"] = ">=0.2.7 < 1.0.0"
      elif kwargs["chatops"] == "flowdock":
        config["hubot::adapter"] = "flowdock"
        config["hubot::env_export"].update({
          "HUBOT_FLOWDOCK_API_TOKEN":       kwargs["flowdock-token"],
          "HUBOT_FLOWDOCK_LOGIN_EMAIL":     kwargs["flowdock-email"],
          "HUBOT_FLOWDOCK_LOGIN_PASSWORD":  kwargs['flowdock-password']
        })
        config["hubot::dependencies"]["hubot-flowdock"] = ">=0.7.6 < 1.0.0"
      elif kwargs["chatops"] == "slack":
        config["hubot::adapter"] = "slack"
        config["hubot::env_export"].update({
          "HUBOT_SLACK_TOKEN": kwargs["slack-token"]
        })
        config["hubot::dependencies"]["hubot-slack"] = ">=3.3.0 < 4.0.0"
      elif kwargs["chatops"] == "hipchat":
        config["hubot::adapter"] = "hipchat"
        config["hubot::env_export"].update({
          "HUBOT_HIPCHAT_JID": kwargs["hipchat-jid"],
          "HUBOT_HIPCHAT_PASSWORD": kwargs["hipchat-password"]
        })
        if kwargs["text-hipchat-domain"] != "":
          config["hubot::env_export"]["HUBOT_XMPP_DOMAIN"] = kwargs["text-hipchat-domain"]
        config["hubot::dependencies"]["hubot-hipchat"] = ">=2.12.0 < 3.0.0"
      elif kwargs["chatops"] == "xmpp":
        config["hubot::adapter"] = "xmpp"
        config["hubot::env_export"].update({
          "HUBOT_XMPP_USERNAME": kwargs["xmpp-username"],
          "HUBOT_XMPP_PASSWORD": kwargs["xmpp-password"],
          "HUBOT_XMPP_ROOMS": kwargs["xmpp-rooms"]
        })
        if kwargs["xmpp-host"] != "":
          config["hubot::env_export"]["HUBOT_XMPP_HOST"] = kwargs["xmpp-host"]
        if kwargs["xmpp-port"] != "":
          config["hubot::env_export"]["HUBOT_XMPP_PORT"] = kwargs["xmpp-port"]
        config["hubot::dependencies"]["hubot-xmpp"] = ">=0.1.16 < 1.0.0"

    if not os.path.exists(self.path):
      os.makedirs(self.path)

    with open(self.path+self.configname, 'w') as workroom:
      workroom.write(yaml.dump(config))

    redirect('/install', internal=True)

  @expose(generic=True)
  def data_save(self, hostname, password):
    self.hostname = hostname
    self.password = password

  @expose(generic=True, template='progress.html')
  def install(self):
    return {"hostname": self.hostname}

  @expose(generic=True, template='byob.html')
  def byob(self):
    return {"hostname": (self.hostname or "&lt;hostname&gt;"), "password": self.password or "&lt;password&gt;"}
