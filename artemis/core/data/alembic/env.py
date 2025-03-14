from __future__ import with_statement

import asyncio
import os
from pathlib import Path
import threading
from logging.config import fileConfig

import yaml
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from core.config import CoreConfig
from core.data.schema.base import metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    raise Exception("Not implemented or configured!")

    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    ini_section = config.get_section(config.config_ini_section)
    overrides = context.get_x_argument(as_dictionary=True)
    for override in overrides:
        ini_section[override] = overrides[override]

    core_config = CoreConfig()
    
    with (Path("../../..") / os.environ["ARTEMIS_CFG_DIR"] / "core.yaml").open(encoding="utf-8") as f:
        core_config.update(yaml.safe_load(f))

    connectable = async_engine_from_config(
        ini_section,
        poolclass=pool.NullPool,
        connect_args={
            "charset": "utf8mb4",
            "ssl": core_config.database.create_ssl_context_if_enabled(),
        }
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # there's no event loop
        asyncio.run(run_async_migrations())
    else:
        # there's currently an event loop and trying to wait for a coroutine
        # to finish without using `await` is pretty wormy. nested event loops
        # are explicitly forbidden by asyncio.
        #
        # take the easy way out, spawn it in another thread.
        thread = threading.Thread(target=asyncio.run, args=(run_async_migrations(),))
        thread.start()
        thread.join()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
