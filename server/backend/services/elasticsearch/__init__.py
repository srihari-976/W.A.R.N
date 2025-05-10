# Initialize Elasticsearch services package
from .client import ESClient
from .query import query_events

__all__ = ['ESClient', 'query_events']