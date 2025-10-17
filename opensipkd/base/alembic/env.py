"""Pyramid bootstrap environment. """
import logging
import os
import importlib.machinery
from alembic import context
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)
from sqlalchemy import engine_from_config
from opensipkd.base.models.meta import Base

config = context.config

setup_logging(config.config_file_name)

settings = get_appsettings(config.config_file_name)
logging.info(settings)
target_metadata = Base.metadata

current_dir = os.path.split(__file__)[0]
helper_file = os.path.join(current_dir, 'helpers.py')
loader = importlib.machinery.SourceFileLoader('alembic_helpers', helper_file)
helpers = loader.load_module()

version_table = 'alembic_models'
version_table_schema = 'public'


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=settings['sqlalchemy.url'],
                      version_table=version_table)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(settings, prefix='sqlalchemy.')

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        helpers=helpers,
        version_table=version_table,
        version_table_schema=version_table_schema
    )
    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()