https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux

update-alternatives --list python
if error:
update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python2.5 2
selection
update-alternatives --config python


NGINX

apt-get install python-dev python-pip nginx

sudo apt-get update
sudo apt-get install python-dev python-pip nginx

1. Create env jika belum ada
install uwsgi
../env/bin/pip install uwsgi
pip install uwsgi
pip install PasteScript

1. Create WSGI File::

  nano ~/myapp/wsgi.py


  def application(environ, start_response):
      start_response('200 OK', [('Content-Type', 'text/html')])
      return ["<h1 style='color:blue'>Hello There!</h1>"]

  uwsgi --socket 0.0.0.0:8080 --protocol=http -w wsgi

2. Edit Ini File::

  nano ~/myapp/myapp.ini

  [uwsgi]
  module = wsgi:application
  master = true
  processes = 5
  socket = myapp.sock
  chmod-socket = 664
  vacuum = true
  die-on-term = true

3. Create an Upstart File to Manage the App::

	sudo nano /etc/init/myapp.conf

    description "uWSGI instance to serve myapp"

    start on runlevel [2345]
    stop on runlevel [!2345]

    setuid demo
    setgid www-data

    script
        cd /home/demo/myapp
        . myappenv/bin/activate
        uwsgi --ini myapp.ini
    end script

    sudo start myapp
    ps aux | grep myapp
    sudo stop myapp

3. Configure NGINX::

   Edit Config File

	sudo nano /etc/nginx/sites-available/myapp

    server {
        listen 80;
        server_name server_domain_or_IP;

        location / {
            include         uwsgi_params;
            uwsgi_pass      unix:/home/demo/myapp/myapp.sock;
        }
    }

    sudo service nginx configtest

    sudo service nginx restart


uwsgi --paste config:/opt/env/wiki/development.ini --socket :3031 -H /opt/env



Cara lain
https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/deployment/uwsgi_nginx_systemd.html
/etc/systemd/system/pyramid.service

[Unit]
Description=pyramid app

# Requirements
Requires=network.target

# Dependency ordering
After=network.target

[Service]
TimeoutStartSec=0
RestartSec=10
Restart=always

# path to app
WorkingDirectory=/opt/env/wiki
# the user that you want to run app by
User=app

KillSignal=SIGQUIT
Type=notify
NotifyAccess=all

# Main process
ExecStart=/opt/env/bin/uwsgi --ini-paste-logged /opt/env/wiki/development.ini

[Install]
WantedBy=multi-user.target

https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/deployment/uwsgi_nginx_systemd.html

NGINX

location / {
        proxy_set_header        Host $http_host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;

        client_max_body_size    10m;
        client_body_buffer_size 128k;
        proxy_connect_timeout   60s;
        proxy_send_timeout      90s;
        proxy_read_timeout      90s;
        proxy_buffering         off;
        proxy_temp_file_write_size 64k;
        proxy_pass http://pyramid;
        proxy_redirect          off;
    }
