from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from .client import ESClient

logger = logging.getLogger(__name__)

def query_events(
    query: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_types: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    size: int = 100
) -> List[Dict[str, Any]]:
    """
    Query events from Elasticsearch
    
    Args:
        query: Search query string
        start_time: Start time for filtering
        end_time: End time for filtering
        event_types: List of event types to filter by
        sources: List of event sources to filter by
        size: Maximum number of results to return
        
    Returns:
        List of matching events
    """
    try:
        # Initialize client
        es_client = ESClient()
        
        # Build query
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {"query_string": {"query": query}}
                    ]
                }
            },
            "sort": [{"timestamp": "desc"}],
            "size": size
        }
        
        # Add time range if provided
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            search_query["query"]["bool"]["must"].append({
                "range": {"timestamp": time_range}
            })
            
        # Add event type filter if provided
        if event_types:
            search_query["query"]["bool"]["must"].append({
                "terms": {"type": event_types}
            })
            
        # Add source filter if provided
        if sources:
            search_query["query"]["bool"]["must"].append({
                "terms": {"source": sources}
            })
            
        # Execute search
        response = es_client.search_logs(
            query=query,
            start_time=start_time.isoformat() if start_time else None,
            end_time=end_time.isoformat() if end_time else None
        )
        
        # Extract and return results
        return [hit["_source"] for hit in response["hits"]["hits"]]
        
    except Exception as e:
        logger.error(f"Error querying events: {str(e)}")
        return []

def get_event_count_by_type(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict[str, int]:
    """
    Get event counts grouped by type
    
    Args:
        start_time (datetime, optional): Start time for aggregation
        end_time (datetime, optional): End time for aggregation
        
    Returns:
        dict: Event type counts
    """
    try:
        # Initialize client
        client = ESClient()
        
        # Build aggregation query
        query = {
            'size': 0,
            'aggs': {
                'event_types': {
                    'terms': {
                        'field': 'type',
                        'size': 50
                    }
                }
            }
        }
        
        # Add time range filter
        if start_time or end_time:
            query['query'] = {
                'bool': {
                    'must': [{
                        'range': {
                            'timestamp': {}
                        }
                    }]
                }
            }
            if start_time:
                query['query']['bool']['must'][0]['range']['timestamp']['gte'] = start_time.isoformat()
            if end_time:
                query['query']['bool']['must'][0]['range']['timestamp']['lte'] = end_time.isoformat()
                
        # Execute query
        results = client.search('events', query)
        
        # Process results
        counts = {}
        for bucket in results.get('aggregations', {}).get('event_types', {}).get('buckets', []):
            counts[bucket['key']] = bucket['doc_count']
            
        return counts
        
    except Exception as e:
        logger.error(f"Error getting event counts: {str(e)}")
        return {}

class QueryBuilder:
    """
    Helper class to build ElasticSearch queries for security event retrieval.
    Provides a fluent interface for constructing complex queries.
    """
    
    def __init__(self):
        """Initialize an empty query."""
        self.query = {
            "query": {
                "bool": {
                    "must": [],
                    "should": [],
                    "must_not": [],
                    "filter": []
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "aggs": {}
        }
        self.size = 100
        
    def with_size(self, size):
        """Set the maximum number of results to return."""
        self.size = size
        return self
        
    def with_timerange(self, start_time, end_time=None):
        """
        Add time range filter to the query.
        
        Args:
            start_time (str): ISO format start time or relative time (e.g., "now-24h")
            end_time (str, optional): ISO format end time, defaults to "now"
        """
        range_filter = {
            "range": {
                "@timestamp": {
                    "gte": start_time,
                    "lte": end_time if end_time else "now"
                }
            }
        }
        self.query["query"]["bool"]["filter"].append(range_filter)
        return self
        
    def with_term(self, field, value):
        """Add exact match term filter."""
        term_filter = {"term": {field: value}}
        self.query["query"]["bool"]["filter"].append(term_filter)
        return self
        
    def with_terms(self, field, values):
        """Add multiple terms filter (OR condition)."""
        terms_filter = {"terms": {field: values}}
        self.query["query"]["bool"]["filter"].append(terms_filter)
        return self
        
    def with_match(self, field, value):
        """Add full-text match query."""
        match_query = {"match": {field: value}}
        self.query["query"]["bool"]["must"].append(match_query)
        return self
        
    def with_wildcard(self, field, pattern):
        """Add wildcard pattern matching."""
        wildcard_query = {"wildcard": {field: pattern}}
        self.query["query"]["bool"]["must"].append(wildcard_query)
        return self
        
    def exclude_term(self, field, value):
        """Exclude exact match term."""
        term_query = {"term": {field: value}}
        self.query["query"]["bool"]["must_not"].append(term_query)
        return self
        
    def with_aggregation(self, name, agg_type, field, size=10):
        """
        Add an aggregation to the query.
        
        Args:
            name (str): Aggregation name
            agg_type (str): Aggregation type (e.g., "terms", "date_histogram")
            field (str): Field to aggregate on
            size (int): Number of buckets to return
        """
        if agg_type == "terms":
            self.query["aggs"][name] = {
                "terms": {
                    "field": field,
                    "size": size
                }
            }
        elif agg_type == "date_histogram":
            self.query["aggs"][name] = {
                "date_histogram": {
                    "field": field,
                    "calendar_interval": "day"  # Default to daily intervals
                }
            }
        return self
        
    def build(self):
        """Return the constructed query."""
        result = self.query.copy()
        if self.size:
            result["size"] = self.size
        return result
        
    # Common security query templates
    
    @classmethod
    def failed_authentication_query(cls, timeframe="now-24h"):
        """
        Create query for failed authentication events.
        
        Args:
            timeframe (str): Time range to search
            
        Returns:
            QueryBuilder: Configured query builder
        """
        return cls() \
            .with_timerange(timeframe) \
            .with_match("event.category", "authentication") \
            .with_match("event.outcome", "failure") \
            .with_aggregation("top_users", "terms", "user.name") \
            .with_aggregation("top_sources", "terms", "source.ip")
            
    @classmethod
    def malware_detection_query(cls, timeframe="now-7d"):
        """
        Create query for malware detection events.
        
        Args:
            timeframe (str): Time range to search
            
        Returns:
            QueryBuilder: Configured query builder
        """
        return cls() \
            .with_timerange(timeframe) \
            .with_match("event.category", "malware") \
            .with_aggregation("malware_types", "terms", "threat.technique.name") \
            .with_aggregation("affected_hosts", "terms", "host.name")
            
    @classmethod
    def anomalous_network_query(cls, timeframe="now-12h"):
        """
        Create query for anomalous network traffic.
        
        Args:
            timeframe (str): Time range to search
            
        Returns:
            QueryBuilder: Configured query builder
        """
        return cls() \
            .with_timerange(timeframe) \
            .with_match("event.category", "network") \
            .with_match("event.type", "anomaly") \
            .with_aggregation("top_destinations", "terms", "destination.ip") \
            .with_aggregation("protocols", "terms", "network.protocol")