import threading

MAX_DB_IMAGE_COUNT: int = 10
NEW_IMG_EVENT: threading.Event = threading.Event()