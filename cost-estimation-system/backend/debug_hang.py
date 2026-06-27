import threading
import sys
import traceback
import time

def monitor():
    time.sleep(5)
    print("--- DUMPING THREADS ---")
    for thread_id, frame in sys._current_frames().items():
        print(f"\nThread ID: {thread_id}")
        traceback.print_stack(frame, file=sys.stdout)
    print("-----------------------")
    sys.exit(1)

t = threading.Thread(target=monitor, daemon=True)
t.start()

print("Starting import...")
import main
print("Import finished successfully!")
