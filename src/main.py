#!/usr/bin/env python3
"""
Main entry point for contractor enrichment system
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.config import config
from src.database.connection import db_pool

# Create logs directory if it doesn't exist
logs_dir = Path("/app/logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(logs_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ContractorEnrichmentSystem:
    """Main application class"""
    
    def __init__(self):
        self.running = False
        self.shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the system"""
        logger.info("Initializing Contractor Enrichment System...")
        
        # Validate configuration
        if not config.validate():
            raise RuntimeError("Configuration validation failed")
        
        # Initialize database pool
        await db_pool.initialize()
        
        logger.info("System initialization completed")
    
    async def start(self):
        """Start the main application"""
        logger.info("Starting contractor enrichment processing...")
        
        self.running = True
        
        try:
            # Main processing loop would go here
            # For now, just wait for shutdown
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Processing cancelled")
        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down contractor enrichment system...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Close database pool
        await db_pool.close()
        
        logger.info("Shutdown completed")
    
    def handle_signal(self, signum):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())


async def main():
    """Main entry point"""
    app = ContractorEnrichmentSystem()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        app.handle_signal(signum)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        await app.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))