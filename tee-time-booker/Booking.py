import DB as DB_module
import rsa
import tee_time_booker
from datetime import datetime, time, timedelta, date
import time as time_module
import schedule
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB = DB_module.Database()

def process_bookings():
    """Process bookings that need to be made today"""
    current_time = datetime.now()
    logger.info(f"Processing bookings at exactly {current_time.strftime('%H:%M:%S.%f')[:-3]}")
    
    try:
        data = DB.execute_query("SELECT * FROM bookings")
        processed_bookings = []
        
        for booking in data:
            booking_date = datetime.strptime(booking["date"], "%Y/%m/%d").date()
            booking_open_date = booking_date - timedelta(days=8)
            
            # Check if booking opens today
            if booking_open_date == date.today():
                logger.info(f"Processing booking ID {booking['id']} for {booking['username']} on {booking['date']} at {booking['time']}")
                
                try:
                    # Decrypt password and run booking
                    decrypted_password = rsa.decrypt(
                        bytes.fromhex(booking["password"]), 
                        rsa.PrivateKey.load_pkcs1(booking["private_key"].encode())
                    ).decode()
                    
                    result = tee_time_booker.run(
                        booking["username"], 
                        decrypted_password, 
                        booking["club"], 
                        [booking["time"]], 
                        booking["date"], 
                        *booking["players"].split(",")
                    )
                    
                    logger.info(f"Booking attempt completed for {booking['username']}: {result}")
                    processed_bookings.append(booking['id'])
                    
                except Exception as e:
                    logger.error(f"Error processing booking {booking['id']}: {e}")
            
            # Clean up old bookings (older than 8 days ago)
            elif booking_date < date.today() - timedelta(days=8):
                logger.info(f"Deleting old booking ID {booking['id']} for date {booking['date']}")
                DB.execute_update("DELETE FROM bookings WHERE id = ?", (booking["id"],))
        
        return processed_bookings
        
    except Exception as e:
        logger.error(f"Error in process_bookings: {e}")
        return []

def wait_for_exact_time():
    """Wait until exactly 7:30:00 AM, then execute bookings"""
    now = datetime.now()
    target_time = now.replace(hour=7, minute=30, second=0, microsecond=0)
    
    # If it's already past 7:30 AM today, schedule for tomorrow
    if now >= target_time:
        target_time += timedelta(days=1)
    
    # Calculate precise sleep time
    sleep_duration = (target_time - now).total_seconds()
    
    logger.info(f"Current time: {now.strftime('%H:%M:%S.%f')[:-3]}")
    logger.info(f"Target time: {target_time.strftime('%H:%M:%S.%f')[:-3]}")
    logger.info(f"Sleeping for {sleep_duration:.3f} seconds")
    
    # Sleep until exactly the target time
    time_module.sleep(sleep_duration)
    
    # Execute bookings at exactly 7:30:00 AM
    process_bookings()

def run_booking_scheduler():
    """Continuous booking scheduler that runs at exactly 7:30:00 AM every day"""
    logger.info("Booking scheduler started - will run at exactly 7:30:00 AM daily")
    
    # Schedule the booking to run at exactly 7:30:00 AM every day
    schedule.every().day.at("07:30:00").do(process_bookings)
    
    while True:
        try:
            # Check if it's time to run any scheduled jobs
            schedule.run_pending()
            
            # Sleep for a longer time to reduce CPU usage and be more responsive to interrupts
            # Using 1 second instead of 0.1 for better performance
            time_module.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Booking scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}")
            time_module.sleep(5)  # Wait 5 seconds before retrying

def main():
    """Main entry point - starts the precise booking scheduler"""
    logger.info("Starting precise booking scheduler - executes exactly at 7:30:00 AM daily")
    logger.info("Bookings will be processed exactly 8 days before the tee time")
    
    try:
        run_booking_scheduler()
    except KeyboardInterrupt:
        logger.info("Booking scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")

def wait_until_time(target_time):
    """Wait until the target time is reached - legacy function"""
    while True:
        now = datetime.now().time()
        if now >= target_time:
            break
        
        # Calculate seconds until target time
        now_datetime = datetime.combine(date.today(), now)
        target_datetime = datetime.combine(date.today(), target_time)
        
        # If target time has passed today, wait until tomorrow
        if target_datetime <= now_datetime:
            target_datetime += timedelta(days=1)
        
        sleep_seconds = (target_datetime - now_datetime).total_seconds()
        
        if sleep_seconds > 60:  # If more than a minute, log and sleep in chunks
            logger.info(f"Waiting {sleep_seconds/60:.1f} minutes until {target_time}")
            time_module.sleep(60)  # Sleep for 1 minute at a time
        else:
            time_module.sleep(sleep_seconds)
            break

def main_legacy():
    """Legacy main loop - kept for reference"""
    target_time = time(7, 30)  # 7:30 AM
    logger.info("Booking scheduler started. Target time: 7:30 AM")
    
    while True:
        try:
            # Wait until 7:30 AM
            wait_until_time(target_time)
            
            logger.info("It's 7:30 AM - processing bookings...")
            processed = process_bookings()
            
            if processed:
                logger.info(f"Processed {len(processed)} bookings")
            else:
                logger.info("No bookings to process today")
            
            # Wait until tomorrow (sleep for 23 hours 59 minutes to avoid missing the time)
            logger.info("Waiting until tomorrow...")
            time_module.sleep(86000)  # 23 hours 59 minutes = 86340 seconds, just in case of time drift 86000
            
        except KeyboardInterrupt:
            logger.info("Booking scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time_module.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    main()