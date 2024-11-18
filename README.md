# Basis Aplikasi openSIPKD

Ini adalah basis dari seluruh aplikasi openSIPKD.

# Pemasangan

## Pasang paket Debian yang dibutuhkan::

    $ sudo apt install libxml2-dev libxslt1-dev libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

## Buat Python Virtual Environment:
Biasanya pada home directory::

    $ python3 -m venv ~/env
    $ ~/env/bin/pip install --upgrade pip setuptools
    $ ~/env/bin/pip install wheel

## Instalasi

### Production:

    $ ~/env/bin/pip install git+https://git.opensipkd.com/aa.gusti/base.git@latest
    $ cp ~/env/etc/live_opensipkd.tpl  ~/env/etc/live_opensipkd.ini 

### Install Development::
    $ source ~/env/bin/activate 
    $ mkdir apps
    $ cd apps
    $ git clone https://git.opensipkd.com/aa.gusti/base.git@latest
    $ env/bin/pip install -e base[dev]
    $ cp ~/env/etc/test_opensipkd.tpl  ~/env/etc/test_opensipkd.ini 

## Sesuaikan konfigurasi 
Konfigurasi tergantung pada jenis instalasi ``test_opensipkd.ini`` atau 
``live_opensipkd.ini``pada baris berikut ini::

### Database Koneksi:
    [app:main]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    session.url = postgresql://user:password@localhost:5432/db


    [alembic_ziggurat]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = ziggurat_foundation:migration

    [alembic_base]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = opensipkd.base:alembic

### Login/Register:
    [app:main]
    captcha_files=
    # static folder untuk image captcha
    reg_captcha = 1
    # saat registrasi diwajibkan menggunakan captcha
    reg_idcard = 1
    # saat registrasi diwajibkan mengisi kode/nik pengguna
    # akan menampilkan pula upload file id card
    reg_verify = 1
    # Registrasi memrlukan verifikasi terlebih dahulu sebelum dapat login
    reg_form =
    # diisi route registrasi default "register" jika dikosongkan
    login_tpl =
    # diisi nama template login apabila akan menggunakan template yang berbeda


### Handling Log File:

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
### Google Integrated dan Custom Register Form
Aplikasi sudah bisa terintegrsi dengan google oauth2

Konfigurasi merupakan bagian dari "main"

```
    [app:main]
    allow_register = True
    google-signin-client-id = id oauth2 client dari google
```


## Buat tabelnya::
    
Perintah untuk membuat tabel

    $ ~/env/bin/initialize_opensipkd_db [file_config]

Contoh:

    $ ~/env/bin/initialize_opensipkd_db ~/env/etc/test_opensipkd.ini

##Jalankan::

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
# Migrasi
Karena ada penambahan dari fungsi table route berfungsi sebagai menu 
generator, maka diperlukan upgrade khusus bagi aplikasi lama
```
alembic -c config_file -n alembic_models upgrade head 
```
Tambahkan Konfigurasi berikut ini
```
    [alembic_models]
    sqlalchemy.url = postgresql://user:password@localhost:5432/db
    script_location = opensipkd.models:alembic
```
# Virtual Directory

## Setting Ini File
### Ubah `[app:main]` jadi `[app:opensipkd]`
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
        
        client_max_body_size    10m;
        client_body_buffer_size 128k;
        proxy_connect_timeout   60s;
        proxy_send_timeout      90s;
        proxy_read_timeout      90s;
        proxy_buffering         off;
        proxy_temp_file_write_size 64k;
        
        proxy_pass http://127.0.0.1:6543/;
        proxy_redirect          off;
    }

```

Other Configuration
```
[server:main]
use = egg:waitress#main
host = 0.0.0.0
port = 6543
;port = %(http_port)s digunakan jika port akan menggunakan parameter
trusted_proxy = 10.8.50.23
trusted_proxy_count = 1
trusted_proxy_headers = x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port
clear_untrusted_proxy_headers = yes
url_scheme = https # HTTP or https
```