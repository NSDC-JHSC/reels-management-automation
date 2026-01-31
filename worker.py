import time
from notifications import process_scheduled_notifications

print("📨 Email worker started")

while True:
    try:
        results = process_scheduled_notifications()
        if results:
            print("Emails processed:", results)
    except Exception as e:
        print("Worker error:", e)

    time.sleep(300)
