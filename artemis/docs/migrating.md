# Migrating from an older build of ARTEMiS
If you haven't updated artemis in a while, you may find that configuration options have moved, been renamed, or no longer exist. This document exists to help migrate from legacy versions of artemis to newer builds.

## Dependancies
Make sure your dependiences are up to date with what's required to run artemis. A simple `pip install -r requirements.txt` will get you up to date.

## Database
Database migration is required if you are using a version of artemis that still uses the old custom-rolled database versioning system (raw SQL scripts). Artemis now uses alembic to manage database versioning, and you will need to move to this new system.

**BEFORE DOING ANY DATABASE WORK, ALWAYS MAKE SURE YOU HAVE FUNCTIONAL, UP-TO-DATE BACKUPS!!**

For almost all situations, simply running `python dbutils.py migrate` will do the job. This will upgrade you to the latest version of the old system, move you over to alembic, then upgrade you to the newest alembic version. If you encounter any errors or data loss, you should report this as a bug to our issue tracker.

## Configuration
Configuration management is the sewage cleaning of the sysadmin world. It sucks and nobody likes to do it, but it needs to be done or everyone ends up in deep shit. This section will walk through what configuration options have changed, and how to set them properly.

### core.yaml
`title`->`hostname` is now `server`->`hostname`. This hostname is what gets sent to clients in response to auth requests, so it should be both accessable from whereever the client is, and point properly to the title server.

With the move to starlette and uvicorn, different services now run as seperate USGI applications. `billing`->`standalone` and `allnet`->`standalone` are flags that determine weather the service runs as a stand-alone service, on it's own seperate port, or as a part of the whole application. For example, setting `billing`->`standalone` to `True` will cause a seperate instance of the billing server to spin up listening on 8443 with SSL using the certs listed in the config file. Setting it to `False` will just allow the main server to also serve `/request/` and assumes that something is standing in front of it proxying 8443 SSL to whatever `server`->`port` is set to.

Beforehand, if `server`->`is_develop` was `False`, the server assumed that there was a proxy standing in front of it, proxying requests to proper channels. This was, in hindsight, a very dumb assumption. Now, `server`->`is_using_proxy` is what flags the server as having nginx or another proxy in front of it. The effects of setting this to true are somewhat game-dependant, but generally artemis will use the port listed in `server`->`proxy_port` (and `server`->`proxy_port_ssl` for SSL connections, as defined by the games) instead of `server`->`port`. If set to 0, `server`->`proxy_port` will default to what `server`->`port` (and `server`->`proxy_port_ssl` will default to 443) make sure to set them accordingly. Note that some title servers have their own needs and specify their own specific ports. Refer to [game_specific_info.md](docs/game_specific_info.md) for more infomation. (For example, pokken requires SSL using an older, weaker certificate, and always requires the port to be sent even if it's port 443)

`index.py`'s args have changed. You can now override what port the title server listens on with `-p` and tell the server to use ssl with `-s`.

Rather then having a `standalone` config variable, the frontend is a seperate wsgi app entirely. Having `enable` be `True` will launch it on the port specified in the config file. Otherwise, the fontend will not run.

`title`->`reboot_start_time`/`reboot_end_time` allow you to specify when the games should be told network maintanence is happening. It's exact implementation depends on the game. Do note that many games will beave unexpectly if `reboot_end_time` is not `07:00`.

If you wish to make use of aimedb's SegaAuthId system to better protect the few title servers that actually use it, set `aimedb`->`id_secret` to base64-encoded random bytes (32 is a good length) using something like `openssl rand -base64 64`. If you intend to use the frontend, the same thing must be done for `frontend`->`secret` or you won't be able to log in.

`mucha`'s only option is now just log level.

`aimedb` now has it's own `listen_address` field, in case you want to proxy everything but aimedb, so it can still listen on `0.0.0.0` instead of `127.0.0.1`.
