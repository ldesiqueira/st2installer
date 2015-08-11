# StackStorm installer

An installer UI for StackStorm initial setup. This is a part of [st2workroom](https://github.com/StackStorm/st2workroom) environment and shouldn't normally be run or cloned separately unless you want to develop on the installer itself.

## Installation

Installer utilizes Python backend with [Pecan](http://pecanpy.org) and a jQuery frontend (because, as we all know, [jQuery is really great and does all things](http://i.imgur.com/ifO2JrX.gif)). It's WSGI-compliant and meant to be launched on a server such as uWSGI.

If you want to test it on your own server, there are some easy steps to begin after you clone either `master` (most recent version) or `stable` (used with the current `st2workroom`):

#### 1. Dependencies
The installer depends on `uwsgi`, `pecan`, `pycrypto` and `pyyaml`. Install it:
```
python setup.py install
```

#### 2. Mock Puppet command
If you don't want the installer to launch Puppet, either make a symlink at /usr/bin/puprun to a dummy output script or change line 10 in `st2installer/controllers/root.py` to utilize any mock output command. There's a Python script with mock output provided for your convenience in `test/output.py`:
```
command = 'python test/output.py'
```
It may be necessary to include full path. Obviously, **do not** commit this change.


#### 3. uWSGI
Launch the server:
```
uwsgi --http :9090 --wsgi-file app.wsgi
```
You can also launch any other WSGI server of your choosing.

## Development

Now you can access installer at `http://localhost:9090/`. Be aware that it locks itself after one full launch so that it won't run twice; if you want to launch it more than once you should manually remove `/tmp/st2installer_lock`.
