"""
Enhanced logging utilities for contractor processing pipeline
"""
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import asyncio
from contextlib import contextmanager


@dataclass
class ContractorProcessingLog:
    """Structured log entry for contractor processing"""
    contractor_id: int
    business_name: str
    processing_start: datetime
    processing_end: Optional[datetime] = None
    search_queries: List[str] = None
    search_results: List[Dict[str, Any]] = None
    chosen_website: Optional[str] = None
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    website_confidence: Optional[float] = None
    classification_confidence: Optional[float] = None
    processing_status: str = "processing"
    error_message: Optional[str] = None
    ai_calls: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.search_queries is None:
            self.search_queries = []
        if self.search_results is None:
            self.search_results = []
        if self.ai_calls is None:
            self.ai_calls = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['processing_start'] = self.processing_start.isoformat()
        if self.processing_end:
            data['processing_end'] = self.processing_end.isoformat()
        return data


class ContractorLogger:
    """Enhanced logger for contractor processing with grouping and structured output"""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("/app/logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Task-local storage for contractor processing logs
        self._task_storage = {}
        
        # Setup structured JSON logger
        self.json_logger = self._setup_json_logger()
        
        # Setup human-readable logger
        self.human_logger = self._setup_human_logger()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'completed': 0,
            'errors': 0,
            'manual_review': 0,
            'start_time': datetime.utcnow()
        }
    
    def _setup_json_logger(self) -> logging.Logger:
        """Setup JSON structured logger with rotation"""
        logger = logging.getLogger('contractor_processing_json')
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # JSON file handler with rotation
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "processing.json",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        
        # JSON formatter
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, 'contractor_data'):
                    return json.dumps(record.contractor_data, default=str)
                return json.dumps({
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName
                })
        
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)
        logger.propagate = False
        
        return logger
    
    def _setup_human_logger(self) -> logging.Logger:
        """Setup human-readable logger"""
        logger = logging.getLogger('contractor_processing_human')
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Human-readable file handler
        human_handler = logging.FileHandler(self.log_dir / "processing.log")
        human_handler.setLevel(logging.INFO)
        
        # Human-readable formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        human_handler.setFormatter(formatter)
        logger.addHandler(human_handler)
        logger.propagate = False
        
        return logger
    
    def _get_task_storage(self):
        """Get task-local storage for current asyncio task"""
        try:
            current_task = asyncio.current_task()
            if current_task is None:
                return None
            task_id = id(current_task)
            if task_id not in self._task_storage:
                self._task_storage[task_id] = {
                    'contractor_log': None,
                    'log_buffer': []
                }
            return self._task_storage[task_id]
        except RuntimeError:
            return None
    
    @contextmanager
    def contractor_processing(self, contractor_id: int, business_name: str):
        """Context manager for contractor processing with grouped logging"""
        # Get task storage
        task_storage = self._get_task_storage()
        if not task_storage:
            # Fallback to sequential processing if no task context
            yield self
            return
        
        # Initialize contractor log
        task_storage['contractor_log'] = ContractorProcessingLog(
            contractor_id=contractor_id,
            business_name=business_name,
            processing_start=datetime.utcnow()
        )
        task_storage['log_buffer'] = []
        
        # Log contractor start
        self._log_contractor_start()
        
        try:
            yield self
        except Exception as e:
            # Log error in enhanced logging
            if task_storage['contractor_log']:
                task_storage['contractor_log'].processing_status = 'error'
                task_storage['contractor_log'].error_message = str(e)
                task_storage['contractor_log'].processing_end = datetime.utcnow()
                self._log_contractor_complete()
            raise
        finally:
            # Complete contractor processing
            if task_storage['contractor_log']:
                if not task_storage['contractor_log'].processing_end:
                    task_storage['contractor_log'].processing_end = datetime.utcnow()
                self._log_contractor_complete()
                
                # Update statistics
                self._update_stats()
            
            # Clear task-local storage
            task_storage['contractor_log'] = None
            task_storage['log_buffer'] = []
    
    def _log_contractor_start(self):
        """Log contractor processing start"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
            
        log = task_storage['contractor_log']
        
        # Buffer the start log
        start_log = [
            "=" * 80,
            f"STARTING CONTRACTOR PROCESSING",
            f"Contractor ID: {log.contractor_id}",
            f"Business Name: {log.business_name}",
            f"Start Time: {log.processing_start.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80
        ]
        
        # Store in buffer instead of logging immediately
        task_storage['log_buffer'].extend(start_log)
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'contractor_start',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'timestamp': log.processing_start.isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def _log_contractor_complete(self):
        """Log contractor processing completion"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
            
        log = task_storage['contractor_log']
        
        # Buffer the completion log
        completion_log = [
            "-" * 80,
            f"CONTRACTOR PROCESSING COMPLETE",
            f"Contractor ID: {log.contractor_id}",
            f"Business Name: {log.business_name}",
            f"Processing Status: {log.processing_status}",
            f"Overall Confidence: {log.confidence_score:.3f}" if log.confidence_score is not None else "Overall Confidence: N/A",
            f"Website Confidence: {log.website_confidence:.3f}" if log.website_confidence is not None else "Website Confidence: N/A",
            f"Classification Confidence: {log.classification_confidence:.3f}" if log.classification_confidence is not None else "Classification Confidence: N/A",
            f"Chosen Website: {log.chosen_website}" if log.chosen_website else "Chosen Website: N/A",
            f"Category: {log.category}" if log.category else "Category: N/A",
            f"End Time: {log.processing_end.strftime('%Y-%m-%d %H:%M:%S')}" if log.processing_end else "End Time: N/A"
        ]
        
        if log.error_message:
            completion_log.append(f"Error: {log.error_message}")
        
        completion_log.append("-" * 80)
        
        # Add completion log to buffer
        task_storage['log_buffer'].extend(completion_log)
        
        # Output all buffered logs at once
        for log_line in task_storage['log_buffer']:
            if log_line.startswith("JSON_LOG: "):
                # Extract and log JSON data
                json_data = json.loads(log_line[10:])  # Remove "JSON_LOG: " prefix
                self.json_logger.info("", extra={'contractor_data': json_data})
            else:
                # Log human-readable output
                self.human_logger.info(log_line)
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'contractor_complete',
            **log.to_dict()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_search_query(self, query: str):
        """Log search query"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        log.search_queries.append(query)
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  🔍 SEARCH QUERY: {query}")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'search_query',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'query': query,
            'timestamp': datetime.utcnow().isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_search_results(self, results: List[Dict[str, Any]]):
        """Log search results"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        log.search_results.extend(results)
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  📋 SEARCH RESULTS ({len(results)} found):")
        for i, result in enumerate(results[:5], 1):  # Show top 5 results
            task_storage['log_buffer'].append(f"    {i}. {result.get('title', 'N/A')}")
            task_storage['log_buffer'].append(f"       URL: {result.get('url', 'N/A')}")
            task_storage['log_buffer'].append(f"       Snippet: {result.get('snippet', 'N/A')[:100]}...")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'search_results',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'results_count': len(results),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_ai_call(self, tool_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any] = None):
        """Log AI tool call"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        ai_call = {
            'tool_name': tool_name,
            'input_data': input_data,
            'output_data': output_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        log.ai_calls.append(ai_call)
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  🤖 AI TOOL CALL: {tool_name}")
        task_storage['log_buffer'].append(f"    Input: {json.dumps(input_data, indent=6)}")
        if output_data:
            task_storage['log_buffer'].append(f"    Output: {json.dumps(output_data, indent=6)}")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'ai_call',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'ai_call': ai_call
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_website_selection(self, website: str, confidence: float):
        """Log website selection"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        log.chosen_website = website
        log.website_confidence = confidence
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  🌐 WEBSITE SELECTED: {website}")
        task_storage['log_buffer'].append(f"    Confidence: {confidence:.3f}")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'website_selection',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'website': website,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_classification(self, category: str, confidence: float):
        """Log classification results"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        log.category = category
        log.classification_confidence = confidence
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  🏷️  CLASSIFICATION: {category}")
        task_storage['log_buffer'].append(f"    Confidence: {confidence:.3f}")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'classification',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'category': category,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_final_result(self, confidence_score: float, processing_status: str, error_message: str = None):
        """Log final processing result"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        log.confidence_score = confidence_score
        log.processing_status = processing_status
        log.error_message = error_message
        
        # Buffer human-readable output
        task_storage['log_buffer'].append(f"  ✅ FINAL RESULT:")
        task_storage['log_buffer'].append(f"    Overall Confidence: {confidence_score:.3f}")
        task_storage['log_buffer'].append(f"    Processing Status: {processing_status}")
        if error_message:
            task_storage['log_buffer'].append(f"    Error: {error_message}")
        
        # JSON output (buffered like human-readable logs)
        json_log_entry = {
            'event': 'final_result',
            'contractor_id': log.contractor_id,
            'business_name': log.business_name,
            'confidence_score': confidence_score,
            'processing_status': processing_status,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        task_storage['log_buffer'].append(f"JSON_LOG: {json.dumps(json_log_entry)}")
    
    def log_batch_progress(self, batch_number: int, total_processed: int, batch_results: Dict[str, int]):
        """Log batch processing progress"""
        # Human-readable output
        self.human_logger.info("=" * 60)
        self.human_logger.info(f"BATCH {batch_number} COMPLETED")
        self.human_logger.info(f"Total Processed: {total_processed}")
        self.human_logger.info(f"Batch Results: {batch_results}")
        self.human_logger.info("=" * 60)
        
        # JSON output
        self.json_logger.info("", extra={'contractor_data': {
            'event': 'batch_progress',
            'batch_number': batch_number,
            'total_processed': total_processed,
            'batch_results': batch_results,
            'timestamp': datetime.utcnow().isoformat()
        }})
    
    def log_periodic_stats(self, stats: Dict[str, Any]):
        """Log periodic processing statistics"""
        # Human-readable output
        self.human_logger.info("📊 PERIODIC STATS:")
        for status, data in stats.items():
            if isinstance(data, dict):
                count = data.get('count', 0)
                avg_confidence = data.get('avg_confidence', 0)
                self.human_logger.info(f"  {status.title()}: {count} records, avg confidence: {avg_confidence:.3f}")
            else:
                self.human_logger.info(f"  {status.title()}: {data}")
        
        # JSON output
        self.json_logger.info("", extra={'contractor_data': {
            'event': 'periodic_stats',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }})
    
    def _update_stats(self):
        """Update processing statistics"""
        task_storage = self._get_task_storage()
        if not task_storage or not task_storage['contractor_log']:
            return
        
        log = task_storage['contractor_log']
        if not log:
            return
        
        self.stats['total_processed'] += 1
        
        if log.processing_status == 'completed':
            self.stats['completed'] += 1
        elif log.processing_status == 'error':
            self.stats['errors'] += 1
        elif log.processing_status == 'manual_review':
            self.stats['manual_review'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        duration = datetime.utcnow() - self.stats['start_time']
        return {
            **self.stats,
            'duration_seconds': duration.total_seconds(),
            'records_per_minute': (self.stats['total_processed'] / max(duration.total_seconds() / 60, 1))
        }


# Global logger instance
contractor_logger = ContractorLogger() 