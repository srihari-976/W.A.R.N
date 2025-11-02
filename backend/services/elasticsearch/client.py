from elasticsearch import Elasticsearch, helpers
import logging
from typing import Dict, Any, Optional, List, Union
from backend.config import Config
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class ESClient:
    def __init__(self, 
                 host: str = "http://localhost:9200",
                 username: str = "elastic",
                 password: str = "changeme",
                 index_prefix: str = "security_events"):
        """Initialize Elasticsearch client"""
        self.host = host
        self.username = username
        self.password = password
        self.index_prefix = index_prefix
        
        # Initialize client
        try:
            self.es = Elasticsearch(
                host,
                basic_auth=(username, password),
                verify_certs=False
            )
            if self.es.ping():
                logger.info("Successfully connected to Elasticsearch")
            else:
                logger.error("Failed to connect to Elasticsearch")
                self.es = None
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {str(e)}")
            self.es = None
            
        # Create index if it doesn't exist
        if self.es:
            self._create_index()

    def _create_index(self):
        """Create index with proper mappings if it doesn't exist"""
        index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
        
        if not self.es.indices.exists(index=index_name):
            mappings = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "event_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "source_ip": {"type": "ip"},
                        "user_id": {"type": "keyword"},
                        "asset_id": {"type": "keyword"},
                        "details": {"type": "object"},
                        "anomaly_score": {"type": "float"},
                        "is_anomaly": {"type": "boolean"},
                        "detection_time": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "refresh_interval": "1s"
                }
            }
            
            try:
                self.es.indices.create(index=index_name, body=mappings)
                logger.info(f"Created index {index_name}")
            except Exception as e:
                logger.error(f"Error creating index: {str(e)}")
                raise

    def index_event(self, event: Dict[str, Any]) -> bool:
        """
        Index a single security event
        
        Args:
            event: Event dictionary to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False
            
        try:
            # Add timestamp if not present
            if 'timestamp' not in event:
                event['timestamp'] = datetime.utcnow().isoformat()
                
            # Get current index name
            index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
            
            # Index the event
            response = self.es.index(
                index=index_name,
                document=event,
                refresh=True
            )
            
            return response['result'] == 'created'
            
        except Exception as e:
            logger.error(f"Error indexing event: {str(e)}")
            return False

    def bulk_index_events(self, events: List[Dict[str, Any]]) -> bool:
        """
        Bulk index multiple security events
        
        Args:
            events: List of event dictionaries to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.es:
            return False
            
        try:
            # Get current index name
            index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
            
            # Prepare bulk actions
            actions = [
                {
                    "_index": index_name,
                    "_source": event
                }
                for event in events
            ]
            
            # Perform bulk indexing
            success, failed = helpers.bulk(
                self.es,
                actions,
                refresh=True,
                raise_on_error=False
            )
            
            if failed:
                logger.warning(f"Failed to index {len(failed)} events")
                
            return success > 0
            
        except Exception as e:
            logger.error(f"Error bulk indexing events: {str(e)}")
            return False

    def search_events(self, 
                     query: Dict[str, Any],
                     size: int = 100,
                     from_: int = 0) -> List[Dict[str, Any]]:
        """
        Search for security events
        
        Args:
            query: Elasticsearch query
            size: Number of results to return
            from_: Starting offset
            
        Returns:
            List of matching events
        """
        if not self.es:
            return []
            
        try:
            # Get current index name
            index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y.%m')}"
            
            # Execute search
            response = self.es.search(
                index=index_name,
                body=query,
                size=size,
                from_=from_
            )
            
            # Extract hits
            hits = response['hits']['hits']
            return [hit['_source'] for hit in hits]
            
        except Exception as e:
            logger.error(f"Error searching events: {str(e)}")
            return []

    def get_anomaly_stats(self, 
                         start_time: Optional[str] = None,
                         end_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about anomalies
        
        Args:
            start_time: Start time in ISO format
            end_time: End time in ISO format
            
        Returns:
            Dictionary containing anomaly statistics
        """
        if not self.es:
            return {}
            
        try:
            # Build query
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"is_anomaly": True}}
                        ]
                    }
                },
                "aggs": {
                    "anomaly_count": {"value_count": {"field": "is_anomaly"}},
                    "avg_score": {"avg": {"field": "anomaly_score"}},
                    "by_severity": {
                        "terms": {"field": "severity"}
                    },
                    "by_type": {
                        "terms": {"field": "event_type"}
                    }
                }
            }
            
            # Add time range if specified
            if start_time or end_time:
                time_range = {"range": {"timestamp": {}}}
                if start_time:
                    time_range["range"]["timestamp"]["gte"] = start_time
                if end_time:
                    time_range["range"]["timestamp"]["lte"] = end_time
                query["query"]["bool"]["must"].append(time_range)
            
            # Execute search
            response = self.es.search(
                index=f"{self.index_prefix}-*",
                body=query,
                size=0
            )
            
            # Process results
            aggs = response['aggregations']
            return {
                "total_anomalies": aggs['anomaly_count']['value'],
                "average_score": aggs['avg_score']['value'],
                "by_severity": {
                    bucket['key']: bucket['doc_count']
                    for bucket in aggs['by_severity']['buckets']
                },
                "by_type": {
                    bucket['key']: bucket['doc_count']
                    for bucket in aggs['by_type']['buckets']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting anomaly stats: {str(e)}")
            return {}

    def delete_old_indices(self, days: int = 90):
        """
        Delete indices older than specified days
        
        Args:
            days: Number of days to keep
        """
        if not self.es:
            return
            
        try:
            # Get all indices
            indices = self.es.indices.get_alias().keys()
            
            # Filter indices by prefix
            security_indices = [
                index for index in indices
                if index.startswith(self.index_prefix)
            ]
            
            # Delete old indices
            for index in security_indices:
                try:
                    self.es.indices.delete(index=index)
                    logger.info(f"Deleted old index {index}")
                except Exception as e:
                    logger.error(f"Error deleting index {index}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error deleting old indices: {str(e)}")

    def get_cluster_health(self) -> Dict[str, Any]:
        """Get Elasticsearch cluster health information"""
        if not self.es:
            return {"status": "disconnected"}
            
        try:
            health = self.es.cluster.health()
            return {
                "status": health["status"],
                "number_of_nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"],
                "relocating_shards": health["relocating_shards"],
                "initializing_shards": health["initializing_shards"],
                "unassigned_shards": health["unassigned_shards"]
            }
        except Exception as e:
            logger.error(f"Error getting cluster health: {str(e)}")
            return {"status": "error", "error": str(e)}

class ElasticSearchClient:
    def __init__(self, hosts=None, index_prefix='security'):
        """
        Initialize ElasticSearch client
        
        Args:
            hosts (list): List of ElasticSearch hosts
            index_prefix (str): Prefix for index names
        """
        self.hosts = hosts or ['http://localhost:9200']
        self.index_prefix = index_prefix
        self.client = None
        
        try:
            self.client = Elasticsearch(
                hosts=self.hosts,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
        except Exception as e:
            logger.error(f"Error initializing ElasticSearch client: {str(e)}")
            
    def search_logs(self, query, start_time=None, end_time=None, size=100):
        """
        Search security logs
        
        Args:
            query (str): Search query
            start_time (str): Start time in ISO format
            end_time (str): End time in ISO format
            size (int): Maximum number of results
            
        Returns:
            dict: Search results
        """
        try:
            if not self.client:
                raise ValueError("ElasticSearch client not initialized")
                
            # Build search query
            search_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "query": query,
                                    "fields": ["*"]
                                }
                            }
                        ]
                    }
                },
                "size": size,
                "sort": [
                    {
                        "@timestamp": {
                            "order": "desc"
                        }
                    }
                ]
            }
            
            # Add time range if specified
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time
                if end_time:
                    time_range["lte"] = end_time
                    
                search_query["query"]["bool"]["filter"] = [
                    {
                        "range": {
                            "@timestamp": time_range
                        }
                    }
                ]
                
            # Execute search
            response = self.client.search(
                index=f"{self.index_prefix}-*",
                body=search_query
            )
            
            # Process results
            hits = response.get('hits', {}).get('hits', [])
            total = response.get('hits', {}).get('total', {}).get('value', 0)
            
            results = []
            for hit in hits:
                source = hit.get('_source', {})
                results.append({
                    'id': hit.get('_id'),
                    'index': hit.get('_index'),
                    'score': hit.get('_score'),
                    'timestamp': source.get('@timestamp'),
                    'data': source
                })
                
            return {
                'total': total,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            return {
                'total': 0,
                'results': []
            }
            
    def index_event(self, event):
        """
        Index a security event
        
        Args:
            event (dict): Event data
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.client:
                raise ValueError("ElasticSearch client not initialized")
                
            # Add timestamp if not present
            if '@timestamp' not in event:
                event['@timestamp'] = datetime.utcnow().isoformat()
                
            # Index event
            response = self.client.index(
                index=f"{self.index_prefix}-events-{datetime.utcnow().strftime('%Y.%m.%d')}",
                body=event
            )
            
            return response.get('result') == 'created'
            
        except Exception as e:
            logger.error(f"Error indexing event: {str(e)}")
            return False
            
    def get_event_stats(self, start_time=None, end_time=None):
        """
        Get event statistics
        
        Args:
            start_time (str): Start time in ISO format
            end_time (str): End time in ISO format
            
        Returns:
            dict: Event statistics
        """
        try:
            if not self.client:
                raise ValueError("ElasticSearch client not initialized")
                
            # Build aggregation query
            query = {
                "size": 0,
                "aggs": {
                    "event_types": {
                        "terms": {
                            "field": "event_type.keyword",
                            "size": 10
                        }
                    },
                    "severity_levels": {
                        "terms": {
                            "field": "severity.keyword",
                            "size": 5
                        }
                    },
                    "sources": {
                        "terms": {
                            "field": "source.keyword",
                            "size": 10
                        }
                    }
                }
            }
            
            # Add time range if specified
            if start_time or end_time:
                query["query"] = {
                    "range": {
                        "@timestamp": {}
                    }
                }
                if start_time:
                    query["query"]["range"]["@timestamp"]["gte"] = start_time
                if end_time:
                    query["query"]["range"]["@timestamp"]["lte"] = end_time
                    
            # Execute search
            response = self.client.search(
                index=f"{self.index_prefix}-*",
                body=query
            )
            
            # Process results
            aggs = response.get('aggregations', {})
            
            return {
                'event_types': self._process_terms_agg(aggs.get('event_types', {})),
                'severity_levels': self._process_terms_agg(aggs.get('severity_levels', {})),
                'sources': self._process_terms_agg(aggs.get('sources', {}))
            }
            
        except Exception as e:
            logger.error(f"Error getting event stats: {str(e)}")
            return {
                'event_types': [],
                'severity_levels': [],
                'sources': []
            }
            
    def _process_terms_agg(self, agg):
        """
        Process terms aggregation results
        
        Args:
            agg (dict): Aggregation results
            
        Returns:
            list: Processed results
        """
        try:
            buckets = agg.get('buckets', [])
            return [
                {
                    'key': bucket.get('key'),
                    'count': bucket.get('doc_count')
                }
                for bucket in buckets
            ]
        except Exception as e:
            logger.error(f"Error processing terms aggregation: {str(e)}")
            return []

    def index_log(self, log_data):
        """Index a log entry in Elasticsearch"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in log_data:
                log_data['timestamp'] = datetime.utcnow().isoformat()
                
            # Index the document
            response = self.client.index(
                index=f"{self.index_prefix}-logs-{datetime.utcnow().strftime('%Y.%m.%d')}",
                body=log_data
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error indexing log: {str(e)}")
            raise

    def delete_old_logs(self, days=30):
        """Delete logs older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Build delete query
            delete_query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "lt": cutoff_date.isoformat()
                        }
                    }
                }
            }
            
            # Execute delete
            response = self.client.delete_by_query(
                index=f"{self.index_prefix}-logs-*",
                body=delete_query
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting old logs: {str(e)}")
            raise

    def index_document(self, index: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> bool:
        """
        Index a document in Elasticsearch
        
        Args:
            index (str): Index name
            document (dict): Document to index
            doc_id (str, optional): Document ID
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Index document
            response = self.client.index(
                index=index,
                document=document,
                id=doc_id,
                refresh=True
            )
            
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return False
            
    def search(self, index: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search documents in Elasticsearch
        
        Args:
            index (str): Index name
            query (dict): Elasticsearch query
            
        Returns:
            dict: Search results
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Execute search
            response = self.client.search(
                index=index,
                body=query
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {'hits': {'total': {'value': 0}, 'hits': []}}
            
    def delete_document(self, index: str, doc_id: str) -> bool:
        """
        Delete a document from Elasticsearch
        
        Args:
            index (str): Index name
            doc_id (str): Document ID
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Delete document
            response = self.client.delete(
                index=index,
                id=doc_id,
                refresh=True
            )
            
            return response['result'] == 'deleted'
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
            
    def update_document(self, index: str, doc_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a document in Elasticsearch
        
        Args:
            index (str): Index name
            doc_id (str): Document ID
            update_data (dict): Data to update
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Update document
            response = self.client.update(
                index=index,
                id=doc_id,
                body={'doc': update_data},
                refresh=True
            )
            
            return response['result'] == 'updated'
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
            
    def create_index(self, index: str, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create an Elasticsearch index
        
        Args:
            index (str): Index name
            mappings (dict, optional): Index mappings
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Check if index exists
            if self.client.indices.exists(index=index):
                logger.warning(f"Index {index} already exists")
                return True
                
            # Create index
            response = self.client.indices.create(
                index=index,
                body={'mappings': mappings} if mappings else None
            )
            
            return response.get('acknowledged', False)
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False
            
    def delete_index(self, index: str) -> bool:
        """
        Delete an Elasticsearch index
        
        Args:
            index (str): Index name
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Delete index
            response = self.client.indices.delete(
                index=index
            )
            
            return response.get('acknowledged', False)
            
        except Exception as e:
            logger.error(f"Error deleting index: {str(e)}")
            return False
            
    def bulk_index(self, index: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Bulk index documents in Elasticsearch
        
        Args:
            index (str): Index name
            documents (list): List of documents to index
            
        Returns:
            bool: Success status
        """
        try:
            if not self.client:
                raise ValueError("Elasticsearch client not initialized")
                
            # Prepare bulk actions
            actions = []
            for doc in documents:
                action = {
                    '_index': index,
                    '_source': doc
                }
                if '_id' in doc:
                    action['_id'] = doc.pop('_id')
                actions.append(action)
                
            # Execute bulk indexing
            response = self.client.bulk(
                operations=actions,
                refresh=True
            )
            
            return not response['errors']
            
        except Exception as e:
            logger.error(f"Error bulk indexing documents: {str(e)}")
            return False