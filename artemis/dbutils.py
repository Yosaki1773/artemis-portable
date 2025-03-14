#!/usr/bin/env python3
import argparse
import asyncio
import logging
from os import W_OK, access, environ, mkdir, path

import yaml

from core.config import CoreConfig
from core.data import Data

async def main():
    parser = argparse.ArgumentParser(description="Database utilities")
    parser.add_argument(
        "--config", "-c", type=str, help="Config folder to use", default="config"
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        help="Version of the database to upgrade/rollback to",
    )
    parser.add_argument("--email", "-e", type=str, help="Email for the new user")
    parser.add_argument("--access_code", "-a", type=str, help="Access code for new/transfer user", default="00000000000000000000")
    parser.add_argument("--message", "-m", type=str, help="Revision message")
    parser.add_argument("action", type=str, help="create, upgrade, downgrade, create-owner, migrate, create-revision, create-autorevision")
    args = parser.parse_args()

    environ["ARTEMIS_CFG_DIR"] = args.config

    cfg = CoreConfig()
    if path.exists(f"{args.config}/core.yaml"):
        cfg_dict = yaml.safe_load(open(f"{args.config}/core.yaml"))
        cfg.update(cfg_dict)

    if not path.exists(cfg.server.log_dir):
        mkdir(cfg.server.log_dir)

    if not access(cfg.server.log_dir, W_OK):
        print(
            f"Log directory {cfg.server.log_dir} NOT writable, please check permissions"
        )
        exit(1)

    data = Data(cfg)

    if args.action == "create":
        await data.create_database()
    
    elif args.action == "upgrade":
        data.schema_upgrade(args.version)

    elif args.action == "downgrade":
        if not args.version:
            logging.getLogger("database").error(f"Version argument required for downgrade")
            exit(1)
        data.schema_downgrade(args.version)

    elif args.action == "create-owner":
        await data.create_owner(args.email, args.access_code)

    elif args.action == "migrate":
        await data.migrate()

    elif args.action == "create-revision":
        await data.create_revision(args.message)

    elif args.action == "create-autorevision":
        await data.create_revision_auto(args.message)

    else:
        logging.getLogger("database").info(f"Unknown action {args.action}")


if __name__ == "__main__":
    asyncio.run(main())
