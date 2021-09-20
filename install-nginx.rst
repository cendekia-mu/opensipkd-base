Instalasi `nginx` dan `uwsgi`
=============================

Install Python Requerement::

    Python3

    $ sudo apt install -y uwsgi-core uwsgi-plugin-python3 python3-cookiecutter \
                          python3-pip python3-venv nginx
                      

1. Buat Struktur Directory pada home Folder::

    $ su - user
    $ mkdir -p wsgi/vassals
    $ mkdir logs
    $ mkdir tmp

2. Buat `wsgi.py` ::

    $ cd wsgi
    $ vi wsgi.py

   Isi degan script berikut ::

    from pyramid.scripts.common import get_config_loader
    app_name    = 'main'
    config_vars = {}
    config_uri  = '/home/{home}/wsgi/app.ini'

    loader = get_config_loader(config_uri)
    loader.setup_logging(config_vars)
    app = loader.get_wsgi_app(app_name, config_vars)


3. copy template file dari aplikasi menjasi `app.ini` dan edit `app.ini` ::

    $cp ../apps/base/test.ini app.ini
    $vi app.ini

   Tambahkan baris berikut ini::

    [uwsgi]
    proj = {app_name} #edit disini samakan dengan directory
    chdir = /home/{user}/apps/base  #edit disini (sesuaikan dengan instalsi)
    homedir = /home/{home}
    processes = 2
    threads = 2
    offload-threads = 2
    stats =  127.0.0.1:9191
    max-requests = 5000
    master = True
    vacuum = True
    enable-threads = true
    harakiri = 60
    chmod-socket = 020
    plugin = python3
    pidfile=%(homedir)/tmp/%(proj).pid
    socket = %(homedir)/tmp/%(proj).sock
    virtualenv = %(homedir)/env
    uid = sambara
    gid = www-data

    # Uncomment `wsgi-file`, `callable`, and `logto` during Part 2 of this tutorial
    wsgi-file = %(homedir)/wsgi/wsgi.py
    callable = app


4. Buat file emperor.ini::

    $ vi emperor.ini

   Isi dengan script berikut::

    [uwsgi]
    proj = sambara
    home = /home/{user}
    emperor = %(home)/wsgi/vassals
    limit-as = 1024
    logto = %(home)/logs/emperor.log
    uid = {user}
    gid = www-data

5. Buat Script Init Pada systemd::

    $ vi /etc/systemd/system/{app_name}.uwsgi.service

   Isi dengan script berikut ini::

    # /lib/systemd/system/emperor.uwsgi.service
    [Unit]
    Description=uWSGI {AppName} Emperor
    After=syslog.target

    [Service]
    ExecStart=/usr/bin/uwsgi --ini /home/{homedir}/wsgi/emperor.ini
    # Requires systemd version 211 or newer
    RuntimeDirectory=uwsgi
    Restart=always
    KillSignal=SIGQUIT
    Type=notify
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target


6. Jalankan dengan systemctl::

    $ systemctl start appname.uwsgi.service

