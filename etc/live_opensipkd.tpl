###
# app configuration
# http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/environment.html
###

[app:main]
use = egg:opensipkd_base
reload_templates = true
devel = true
debug_authorization = false
debug_notfound = false
debug_routematch = false
debug_templates = true
default_locale_name = en

sqlalchemy.url = postgresql://user:password@localhost:5432/db

pyramid.includes =
    pyramid_tm
    pyramid_beaker
    pyramid_mailer
    pyramid_chameleon
    pyramid_rpc.jsonrpc

;Session Configuration
session.type = ext:database
session.secret = s0s3cr3t
session.cookie_expires = true
session.key = WhatEver
session.url = postgresql://user:password@localhost:5432/db
session.timeout = 3000
session.lock_dir = %(here)s/tmp

timezone = Asia/Jakarta
localization = id_ID.UTF-8

static_files = %(here)s/../files
# Static external file uploaded to the system

# Your Organisation Identity
company = Your Company
ibukota   = Your City
departement = Your Departemen
address_1 = Your Address
address_2 = Your Address

;center.phone = 021123456789
;center.mobile = 081311045668

# Mail Configuration
mail.sender_name =
mail.username =
mail.host =
mail.port = 25
mail.password =
mail.tls = False
mail.ssl = False
mail.keyfile =
#SSL key file
mail.certfile =
# SSL certificate file
mail.queue_path	=
# Location of maildir
mail.default_sender =
# Default from address
mail.debug = 0
# SMTP debug level
# mail.sendmail_app = /usr/sbin/sendmail
# Sendmail executable
# mail.sendmail_template =
# {sendmail_app} -t -i -f {sender}	Template for sendmail execution
mail.debug_include_bcc = False
# 	Include Bcc headers when Debugging

# ODT to pdf configuration
unoconv_py =
# openoffice/libreoffice python executable
unoconv_bin =
# Python unoconv script path "/home/[apps]/env/bin/unoconv"

#Modules depreceated
modules =

# Menus to be appear in home page
menus = login:Login
        log:App-Log

app_name = Your Aplocation Name

change_unit = False
departemen_chg_id = 3

# Register config parameter
allow_register = False
google-signin-client-id =
captcha_files=/home/aagusti/tmp
reg_captcha = 1
;reg_idcard = 1
reg_verify = 1
reg_form =
login_tpl =

;Digunakan Apabila Applikasi sebagai subdomain
;[app:main] diubah menjadi [app:opensipkd_base]
;[filter:proxy-prefix]
;use = egg:PasteDeploy#prefix
;prefix = /demo
;
;[pipeline:main]
;pipeline =
;    proxy-prefix
;    opensipkd_base


[server:main]
use = egg:waitress#main
host = 0.0.0.0
port = 6543
;port = %(http_port)s digunakan jika port akan menggunakan parameter

# Begin logging configuration

[loggers]
keys = root, opensipkd, sqlalchemy

[handlers]
keys = console, filelog, tabel

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console, filelog, tabel

[logger_opensipkd]
level = INFO
handlers = 
qualname = opensipkd 

[logger_sqlalchemy]
level = WARN
handlers = 
qualname = sqlalchemy.engine
# "level = INFO" logs SQL queries.
# "level = DEBUG" logs SQL queries and results.
# "level = WARN" logs neither.  (Recommended for production systems.)

[handler_filelog]
class = FileHandler
args = ('app.log','a')
;args = ('%(logfile)s','a') digunakan jika nama log file akan menggunakan parameter
level = INFO
formatter = generic


[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[handler_tabel]
class = opensipkd.base.handlers.SQLAlchemyHandler
args = ()
level = WARN
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s
# End logging configuration


[alembic_ziggurat]
script_location=ziggurat_foundations:migrations
sqlalchemy.url = postgresql://user:password@localhost:5432/db

[alembic_base]
script_location=opensipkd.base:alembic
sqlalchemy.url =  postgresql://user:password@localhost:5432/db
