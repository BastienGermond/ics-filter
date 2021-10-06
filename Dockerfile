FROM python:3.8.10-slim

COPY . .

RUN pip install --use-feature=in-tree-build .

RUN pip install gunicorn==20.1.0

ENV ICS_BLACKLIST_FILE=/opt/ics_filter/ics-events-blacklist

CMD ["gunicorn", "--access-logfile", "-", "--timeout", "120", "-b", "0.0.0.0:8000", "ics_filter:wsgi"]
