Basis Aplikasi OpenSIPKD
========================

Ini adalah basis dari seluruh aplikasi.


Pemasangan
----------

Pasang paket Debian yang dibutuhkan::

    $ sudo apt install libxml2-dev libxslt1-dev libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

Buat Python Virtual Environment::

    $ python3.12 -m venv ~/env
    $ ~/env/bin/pip install --upgrade pip setuptools wheel

Unduh source-nya::

    $ git clone https://git.opensipkd.com/aa.gusti/opensipkd-base -b v5.0

Pasang::

    $ ~/env/bin/pip install opensipkd-base/ 

Buat databasenya. Lalu salin file konfigurasi::

    $ cp development.ini.tpl live.ini

Sesuaikan database profile dan log file. Lalu buat tabelnya::

    $ ~/env/bin/initialize_opensipkd_db live.ini

Jalankan web server::

    $ ~/env/bin/pserve live.ini

Di web browser buka `http://localhost:6543/login <http://localhost:6543>`_
 

Bila Digunakan di Paket Lain
----------------------------

Di paket lainnya pada file ``pyproject.toml`` section ``[project]`` baris ``dependencies`` tambahkan::

    dependencies = [
        ...
        'opensipkd-base @ git+https://git.opensipkd.com/aa.gusti/opensipkd-base.git#beta-4.2',
        ]


Publikasi
---------

Saat dipublikasikan maka pastikan otomatis hidup saat komputer aktif. Silakan lihat
`dokumentasi ini <https://wiki.opensipkd.com/doku.php?id=panduan:python:pyramid-sebagai-daemon>`_
untuk penjelasan lebih lanjut, termasuk konfigurasi Nginx.
