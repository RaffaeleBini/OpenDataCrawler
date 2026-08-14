#!/bin/bash
# Entrypoint for auxiliary CKAN processes (harvest gather/fetch consumers,
# harvest scheduler) that don't serve HTTP traffic. Mirrors the init steps
# that start_ckan.sh performs for the main 'ckan' service (secret keys,
# prerun.py, docker-entrypoint.d scripts) but execs the given command
# (e.g. `ckan harvester gather-consumer`) instead of starting uwsgi.
set -e

if [[ $CKAN__PLUGINS == *"datapusher"* ]]; then
    # Same work-around as start_ckan.sh: prerun.py's db init loads the full
    # plugin stack, and the datapusher plugin refuses to configure() without
    # a token, so set a temporary one now; 01_setup_datapusher.sh below sets
    # the real value.
    echo "Setting a temporary value for ckan.datapusher.api_token"
    ckan config-tool $CKAN_INI ckan.datapusher.api_token=xxx
fi

if grep -qE "SECRET_KEY ?= ?$" ckan.ini
then
    echo "Setting SECRET_KEY in ini file"
    ckan config-tool $CKAN_INI "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe())')"
    ckan config-tool $CKAN_INI "WTF_CSRF_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe())')"
    JWT_SECRET=$(python3 -c 'import secrets; print("string:" + secrets.token_urlsafe())')
    ckan config-tool $CKAN_INI "api_token.jwt.encode.secret=${JWT_SECRET}"
    ckan config-tool $CKAN_INI "api_token.jwt.decode.secret=${JWT_SECRET}"
fi

python3 prerun.py

if [[ -d "/docker-entrypoint.d" ]]
then
    for f in /docker-entrypoint.d/*; do
        case "$f" in
            *.sh)     echo "$0: Running init file $f"; . "$f" ;;
            *.py)     echo "$0: Running init file $f"; python3 "$f"; echo ;;
            *)        echo "$0: Ignoring $f (not an sh or py file)" ;;
        esac
    done
fi

exec "$@"
