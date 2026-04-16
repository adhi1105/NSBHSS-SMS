import threading
import time
import requests
import os
import logging

logger = logging.getLogger(__name__)

def start_pinger():
    """
    Spawns a background thread to ping the application's URL periodically.
    Only activates if RENDER_EXTERNAL_HOSTNAME is present.
    """
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    
    if not hostname:
        logger.info("Pinger: Local environment detected or hostname missing. Heartbeat deactivated.")
        return

    # Interval: 13 minutes (Render sleeps after 15 minutes of inactivity)
    interval = 13 * 60 
    url = f"https://{hostname}/"

    def ping_loop():
        logger.info(f"Pinger: Heartbeat thread initialized. Target: {url}")
        
        # Initial sleep to allow the server to fully start
        time.sleep(30)
        
        while True:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Pinger: Heartbeat successfully dispatched to {url} (Status: 200)")
                else:
                    logger.warning(f"Pinger: Heartbeat attempted to {url} but returned status {response.status_code}")
            except Exception as e:
                logger.error(f"Pinger: Heartbeat failed to reach {url}. Error: {str(e)}")
            
            time.sleep(interval)

    # Daemon thread ensures the pinger doesn't block application shutdown
    pinger_thread = threading.Thread(target=ping_loop, daemon=True)
    pinger_thread.start()
