# scripts/retry_and_log.py
import time, traceback

def retry(fn, tries=3, delay=2):
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            print(traceback.format_exc())
            time.sleep(delay * (attempt+1))
    raise RuntimeError("All retries failed")
