# bitly

This is my submission for the [Bit.ly Backend Coding
Challenge](https://gist.github.com/jctbitly/05044bb3281ca6723bc118babc77afc7).

## Overview
This application was built with Python 3.7, on top of the
[Sanic](https://github.com/huge-success/sanic/tree/84b41123f29e8f52c63c82af6f9279a6edaaf1a0) framework.

## Structure

### Application
The application itself is very small. There is a main `entrypoint.py` script which will
run the Sanic application itself. There's a `handlers` package where we define the code
to handle the registered request paths. Lastly, I created a small `util` package to help
with separation of concerns.
```
.
├── bitly
│   ├── entrypoint.py
│   ├── handlers
│   │   ├── countries.py
│   │   └── __init__.py
│   ├── __init__.py
│   └── util
│       └── __init__.py
```

### Supporting
There are also some small containers that are used for a platform independent way of
running helpful development scripts.

* [black](https://github.com/python/black) is a code formatter.
* [pylint](https://github.com/PyCQA/pylint) is a static linter and code quality tool.
* [pytest](https://github.com/pytest-dev/pytest) is my preferred test runner.

```
├── ci
│   ├── black
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── pylint
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── pytest
│       ├── Dockerfile
│       └── entrypoint.sh
```

All of these containers are purpose built to abstract away needing specific Python
dependencies to be installed locally to your computer.

## Instructions
> a list of dependencies of your project, as well as how to install them (we may not be
> experts in your chosen language, framework, and tools)

> instructions for running your application (you may include a Dockerfile or a Makefile,
> but this is not a requirement)

All you need to run the application is to have
[make](https://www.gnu.org/software/make/) and [docker](https://www.docker.com/)
installed.

The included make recipes all wrap docker containers which will be built on demand, and
run whatever you need them to.

You can type `make help` to get the following output:
```
help                           View help information
format                         Formats the code to the `black` standard
lint                           Runs `pylint`
test                           Runs `pytest`
html_coverage                  Runs `pytest` and writes out a coverage report in html
check                          Runs code quality checks
build                          Build the final container for running this application
run                            Run this application locally, within a container (Requires port 8000)
clean                          Deletes the Docker images that have been built to run this application
```

## Endpoints
>descriptions of any endpoints you are exposing, along with example requests (curl or similar is fine)

There is a single endpoint that's exposed in this application: `/v1/countries/metrics`.

Example request using [httpie](https://github.com/jakubroztocil/httpie):
```
⇒  http :8000/v1/countries/metrics Authorization:"Bearer $YOUR_ACCESS_KEY" -v
GET /v1/countries/metrics HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Authorization: Bearer $YOUR_ACCESS_KEY
Connection: keep-alive
Host: localhost:8000
User-Agent: HTTPie/1.0.2



HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 91
Content-Type: application/json
Keep-Alive: 5

{
    "metrics": {
        "DE": 0.0333333333,
        "NL": 0.1,
        "US": 0.1,
        "type": "clicks"
    },
    "unit": "day",
    "units": 30
}
```

## Misc
> a writeup describing major design decisions that you made
The strategy implemented in this application heavily relies on the fact that the work
that needs to be done is all I/O bound. There's very little business logic that this
application actually has to do. We're merely making a few order dependent requests.

The requests for fetching bitlink ids is all paginated. The format for fetching later
pages of data is consistent, which means we can take the total number of bitlinks that
are reported to us, and infer how many pages we need to request for, which we do
concurrently.

Fetching clicks per country can all be done entirely concurrently as well. Once we've
aggregated the list of bitlink ids from the previous request, we can schedule for all of
the requests to get metric information to happen at once.

Because everything is so network bound, I opted to write the application to make use of
Python's coroutine features. Had the work involved required more CPU usage, I would have
instead opted for an asynchronous queueing based architecture.
