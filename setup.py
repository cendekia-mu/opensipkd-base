import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

line = CHANGES.splitlines()[0]
version = line.split()[0]
requires = [
    'sqlalchemy==1.4.50',
    'wheel',
    'colander==1.8.3',
    'pyramid',
    'pyramid_tm',
    "pyramid_beaker",
    "pyramid_mailer",
    'SQLAlchemy',
    'transaction',
    'waitress',
    'pyramid_beaker',
    'pyramid_mailer',
    'ziggurat-foundations',
    'zope.sqlalchemy',
    'pytz',
    'deform',
    'psycopg2-binary',
    'pyramid_chameleon',
    'pyramid_rpc',
    'requests',
    'sqlalchemy-datatables',
    'py3o.template',
    'wheezy.captcha',
    'icecream',
    'google-api-python-client',
    'google',
    'pyjwt',
    # 'z3c.rml',
    # 'opensipkd-tools @git+https://git.opensipkd.com/aa.gusti/opensipkd-tools.git',
]

dev_requires = [
    'pyramid_debugtoolbar',
    'pytest',
]

setup(
    name='opensipkd_base',
    version=version,
    description='Basis Aplikasi openSIPKD',
    long_description=README + '\n\n' + CHANGES,
    author='Agus Gustiana',
    author_email='aa.gustiana@gmail.com',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    license='Apache Software License',
    keywords='web pyramid pylons base',
    packages=find_packages(),
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require={
        'dev': dev_requires,
    },
    package_data={'opensipkd': [
        'base/views/templates/*.pt',
        'base/static/*.*',
        'base/reports/*.*',
        'base/alembic/*.*',
        'base/alembic/versions/*.*',
        'base/views/*.tpl',
        'base/locale/*.*',

    ], },
    data_files=[('etc', ['etc/live_opensipkd.tpl',
                         'etc/test_opensipkd.tpl', ])],
    include_package_data=True,
    entry_points="""\
        [paste.app_factory]
        main = opensipkd.base:main
        [console_scripts]
        initialize_opensipkd_db = opensipkd.base.scripts.initializedb:main
        import_log = opensipkd.base.scripts.import_log:main
           """,
)
