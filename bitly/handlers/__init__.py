"""
A collection of request handlers to register with the web server
"""
from bitly.handlers.countries import fetch_averaged_metrics_per_country

__all__ = ["fetch_averaged_metrics_per_country"]
