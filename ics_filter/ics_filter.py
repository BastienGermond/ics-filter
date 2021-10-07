#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional

import os
import socketserver
import requests
import json
import argparse
import inquirer
import ics

from datetime import datetime, timedelta
from pathlib import Path


class BlacklistException(Exception):
    """Blacklist base exception class"""


class Blacklist():
    """Provides useful function to store and load calendar blacklist"""
    def __init__(self, path: Path):
        # I don't trust that much input path not being a str even though it's
        # typed as a Path so this will catch this "not supported" cases.
        self.path = Path(path)

        self.blacklist = []

        if self.path.is_file():
            self._load()

    def save(self) -> None:
        with self.path.open('w') as fp:
            json.dump(self.blacklist, fp)

    def _load(self) -> None:
        with self.path.open('r') as fp:
            self.blacklist = json.load(fp)

    def add(self, event_desc: str):
        self.blacklist.append(event_desc)

    def __contains__(self, event_desc: str):
        return event_desc in self.blacklist


class CalendarException(Exception):
    """Calendar base class exception"""


class Calendar():
    def __init__(self, url: Optional[str], pre_load: bool = False,
                 cache_period: timedelta = timedelta(seconds=60)):
        self.calendar = None
        self.url = url
        self.cache_period = cache_period
        self.last_fetch = None
        if pre_load:
            self.fetch(url)

    def fetch(self, url: str = None):
        """fetch calendar from url"""
        if self.last_fetch is not None:
            if datetime.now() - self.last_fetch < self.cache_period:
                return
        if url:
            self.url = url
        if self.url is None:
            raise CalendarException("source url has never been specified")
        r = requests.get(self.url)
        if r.status_code != 200:
            print(f"failed to fetch url: {url} ({r.status_code})")
            return
        self.calendar = ics.Calendar(r.text)
        self.last_fetch = datetime.now()

    def filter(self, blacklist: Blacklist) -> Calendar:
        calendar = self.calendar.clone()
        blacklist_events = set()
        descs = set()
        for event in calendar.events:
            descs.add(event.name)
            if event.name and event.name in blacklist:
                blacklist_events.add(event)

        calendar.events.difference_update(blacklist_events)

        cal = self.clone()
        cal.calendar = calendar
        return cal

    def __repr__(self):
        return self.calendar.__repr__()

    def __str__(self):
        return self.calendar.__str__()

    def clone(self) -> Calendar:
        return Calendar(self.url)


def blacklist_manage(calendar: Calendar, blacklist: Blacklist):
    """manage blacklist

    Add/Remove blacklisted events
    """
    print("Loading events name, this can takes few seconds...")
    calendar.fetch()
    events_name = {event.name for event in calendar.calendar.events}
    all_events = events_name.union(set(blacklist.blacklist))
    questions = [
        inquirer.Checkbox('blacklist',
                          message="Blacklist",
                          choices=list(all_events),
                          default=list(blacklist.blacklist),
                          ),
    ]
    answers = inquirer.prompt(questions)
    blacklist.blacklist = answers['blacklist']
    blacklist.save()
    print("Blacklist saved.")


def get_filtered_calendar(calendar: Calendar, blacklist: Blacklist):
    """get calendar, print it out in stdout"""
    filtered = calendar.filter(blacklist)
    print(filtered)


def serve(calendar: Calendar, blacklist: Blacklist):
    """serve an ics filtered with http.server"""
    import http.server

    print("########################################")
    print("#   Should not be use in production!   #")
    print("########################################\n")

    class IcsFilterHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            calendar.fetch()
            if not calendar:
                self.send_response(500)  # let's assume it's a server error
                self.end_headers()
                return

            cal = calendar.filter(blacklist)
            response = str(cal)
            self.send_response(200)
            self.send_header("Content-type", "text/calendar")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, 'utf-8'))

    with socketserver.TCPServer(("0.0.0.0", 8000), IcsFilterHandler) as httpd:
        print("serving at 0.0.0.0:8000")
        httpd.serve_forever()


def create_app():
    blacklist_file = os.getenv("ICS_BLACKLIST_FILE") or '.ics-events-blacklist'
    blacklist = Blacklist(Path(blacklist_file))

    url = os.getenv("SOURCE_ICS")
    calendar = Calendar(url, cache_period=timedelta(minutes=15))

    def wsgi(env, start_response):
        env = env  # make linter happy
        if env["REQUEST_METHOD"] not in ['GET']:
            start_response('404 Not Found', [])
            return None

        headers = [('Content-type', 'text/calendar; charset=utf-8')]
        response = ""

        status = '200 OK'
        try:
            calendar.fetch()
            filtered = calendar.filter(blacklist)
            response = str(filtered)
        except CalendarException:
            status = '500 Internal Server Error'

        start_response(status, headers)
        yield str(response).encode('utf-8')

    return wsgi


def main():
    # (function, do_we_load_calendar)
    actions = {
        'manage-blacklist': (blacklist_manage, False),
        'get-filtered': (get_filtered_calendar, True),
        'serve': (serve, False),
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=list(actions.keys()))
    parser.add_argument('--source-ics',
                        help="Source ics that will be filtered",
                        default=os.getenv("SOURCE_ICS")
                        )
    parser.add_argument('--blacklist-file',
                        help="filepath to blacklist",
                        default=os.getenv("ICS_BLACKLIST_FILE")
                        )

    args = parser.parse_args()
    url = args.source_ics

    if not url:
        print("You should specify --source-ics if environment variable "
              "SOURCE_ICS is not spectified")
        return

    if not args.blacklist_file:
        print("You should specify --blacklist-file if environment variable "
              "ICS_BLACKLIST_FILE is not spectified")
        return

    action, do_we_load_calendar = actions[args.command]

    blacklist = Blacklist(Path(args.blacklist_file))
    calendar = Calendar(url, pre_load=do_we_load_calendar)

    action(calendar, blacklist)


if __name__ == '__main__':
    main()
