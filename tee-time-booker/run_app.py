#!/usr/bin/env python3
"""
Robust application runner with proper thread management
"""
import os
import sys
import signal
import threading
import time
import logging
from app import app
import Booking

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApplicationManager:
    def __init__(self):
        self.booking_thread = None
        self.running = True
        
    def start_booking_scheduler(self):
        """Start the booking scheduler in a daemon thread"""
        try:
            logger.info("Starting booking scheduler...")
            self.booking_thread = threading.Thread(target=Booking.main, daemon=True, name="BookingScheduler")
            self.booking_thread.start()
            logger.info("Booking scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start booking scheduler: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Give threads a moment to finish
        if self.booking_thread and self.booking_thread.is_alive():
            logger.info("Waiting for booking scheduler to finish...")
            time.sleep(2)
        
        logger.info("Shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Run the Flask application with proper thread management"""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start the booking scheduler
            self.start_booking_scheduler()
            
            # Start Flask app
            logger.info("Starting Flask application...")
            app.run(
                debug=True,
                use_reloader=False,  # Disable reloader to prevent threading issues
                threaded=True,
                host='127.0.0.1',
                port=5000
            )
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    manager = ApplicationManager()
    manager.run()

# code to run
"""
cd .\tee-time-booker\tee-time-booker\
& "D:/Users/jacob/Source/Repos/.venv/Scripts/python.exe" "d:/Users/jacob/Source/Repos/tee-time-booker/tee-time-booker/run_app.py"
"""