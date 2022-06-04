# Basis Aplikasi openSIPKD
========================

Ini adalah basis dari seluruh aplikasi openSIPKD.

Pemasangan
----------

Pasang paket Debian yang dibutuhkan::

    $ sudo apt-get install libxml2-dev libxslt1-dev libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

Buat Python Virtual Environment, biasanya pada home directory::

    $ python3 -m venv ~/env
    $ ~/env/bin/pip install --upgrade pip setuptools

Install Production
------------------

    $ ~/env/bin/pip install git+https://github.com/aagusti/tandur.git
    $ cp ~/env/etc/live_opensipkd.tpl  ~/env/etc/live_opensipkd.ini 

Install Development::
-------------------
    $ source ~/env/bin/activate 
    $ mkdir apps
    $ cd apps
    $ git clone https://git.opensipkd.com/bekasi/base.git@ciamis
    $ env/bin/pip install -e base[dev]
    $ cp ~/env/etc/test_opensipkd.tpl  ~/env/etc/test_opensipkd.ini 

Sesuaikan konfigurasi ``test_opensipkd.ini`` atau ``live_opensipkd.ini``
pada baris berikut ini::

    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    session.url = postgresql://user:password@localhost:5432/db

    [alembic_ziggurat]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = ziggurat_foundation:migration

    [alembic_base]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = opensipkd.base:alembic

    [alembic_tandur]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = tandur:alembic

Handling Log File:
==================

Logging dapat dilakukan console, file atau tabel

    >> Module yang akan di logging
    [loggers]
    keys = root, opensipkd, sqlalchemy

    >> output handler gunakan sesuai kebutuhan tidak perlu semuanya
    [handlers]
    keys = console, file, table


    >> output handler gunakan INFO pada level kalau sedang testing
    [logger_opensipkd]
    level = WARN
    handlers = file, table
    qualname = opensipkd

    [handler_table]
    class = opensipkd.base.handlers.SQLAlchemyHandler
    args = ()
    level = NOTSET #Sebaiknya hanya gunakan NOTSET atau WARN 
    formatter = generic

    [handler_file]
    class = FileHandler
    args = ('/full/path/file.log', 'a')
    level = NOTSET #Sebaiknya hanya gunakan NOTSET atau WARN
    formatter = generic

	[alembic]
	sqlalchemy.url = postgresql://user:password@localhost:5432/db
	script_location = alembic

    ```

Buat tabelnya::

    $ ~/env/bin/initialize_opensipkd_db ~/env/etc/test_opensipkd.ini

Jalankan::

    $ ~/env/bin/pserve --reload test.ini

# Penggunaan Proxy

## Apache::

Tambahkan line berikut ini didalam ``<VirtualHost>``::
```
        ProxyRequests Off
        ProxyPreserveHost On
        ProxyPass / http://server:port/
        ProxyPassReverse / http://server:port/
        <Proxy *>
            allow from all
        </Proxy>
```
Contoh::
```
    <VirtualHost ip:80>
        SuexecUserGroup "#uid" "#gid"
        ServerName antrian.opensipkd.com
        ServerAlias www.antrian.opensipkd.com

        ProxyRequests Off
        ProxyPreserveHost On
        ProxyPass / http://localhost:6552/
        ProxyPassReverse / http://localhost:6552/
        <Proxy *>
            allow from all
        </Proxy>
    </VirtualHost>
```

# Virtual Directory

## Setting Ini File
### Ubah `[app:ain]` jadi `[app:opensipkd]`
```
    ;[app:main]
    [app:opensipkd_base]
    trusted_proxy_headers = "forwarded x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port"
    url_prefix='/virtualdir'  ; nama cirtual direktory 
```

Tambahkan blok berikut ini dibawah ini file

```
[filter:proxy-prefix]
use = egg:PasteDeploy#prefix
prefix = /virtualdir ; nama virtual directory

[pipeline:main]
pipeline =
    proxy-prefix
    opensipkd_base
```


## Nginx::
```
    location /virtualdir{
        return 302 /virtualdir/;
    }
    location /virtualdir/ {
        # First attempt to serve request as file, then
        # as directory, then fall back to displaying a 404.
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host:$server_port;
        proxy_set_header X-Forwarded-Port $server_port;
        
        proxy_pass http://127.0.0.1:6543/;
    }

```

