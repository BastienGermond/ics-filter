# ICS Filter

This application serves as a relay between an ics provider (through HTTP) and
an application, it remove blacklisted elements from the calendar before sending
it back.

Currently, it's hard configured to cache for 60 seconds a fetch from source
ics for performance reason and to prevent source of DDoS.

## Environment variable

* **Mandatory** `SOURCE_ICS`: HTTP/HTTPS url to your ics provider (e.g.
  https://chronosvenger.me/?classe=GISTRE.ics)
* **Mandatory** `ICS_BLACKLIST_FILE`: Path where the blacklist file will be
  read or saved.

## How to launch a test server ?

You can test it by invoking `ics_filter/ics_filter.py serve` which will deploy
an http.server bind to 0.0.0.0:8000 (hardcoded values).

**Warning: This must not be used in production.**

## How to use in production ?

You can get an wsgi application with `create_app()` function or the module
variable `wsgi`, the easiest way to use production WSGI server such as for
example
[Waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/index.html)
or [Gunicorn](https://gunicorn.org/#docs).

_Examples:_

```
gunicorn \
      --env 'SOURCE_ICS=https://chronosvenger.me/?classe=GISTRE.ics' \
      --env 'ICS_BLACKLIST_FILE=.calendar-blacklist' \
      --access-logfile - -b 0.0.0.0:8000 'ics_filter:wsgi'
```

## Docker

https://hub.docker.com/r/synapzee/ics-filter

By default, the blacklist file will be stored at
`/opt/ics_filter/ics-events-blacklist`.

_Example on how to use:_

Create in your host 
To start ics-filter, will be served inside with Gunicorn and exposed by the
port 8000:

```
docker run -d --name ics-filter \
    -v /opt/ics_filter:/opt/ics_filter \
    -p 8000:8000 \
    -e SOURCE_ICS='<your_ics_source>' \
    synapzee/ics-filter
```

Add or remove events in blacklist:

```
docker run -it ics-filter \
    -v /opt/ics_filter:/opt/ics_filter \
    -e SOURCE_ICS='<your_ics_source>' \
    synapzee/ics-filter
```

**Note**: You must restart your docker instance for changes to take effects.
