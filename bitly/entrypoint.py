"""
Bit.ly Backend Coding Challenge
"""

from sanic import Sanic
from sanic_json_logging import setup_json_logging, NoAccessLogSanic

from bitly.handlers import fetch_averaged_metrics_per_country


def main():
    """
    Main entrypoint of this application
    """
    app = NoAccessLogSanic(__name__)
    setup_json_logging(app)
    app.add_route(
        fetch_averaged_metrics_per_country, "/countries/metrics", version="v1"
    )
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
