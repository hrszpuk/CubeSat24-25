import logging
from functools import wraps

logging.basicConfig(
    filename='vector.log',
    level=logging.INFO,
    format='<%(asctime)s> [%(levelname)s]: %(message)s'
)

def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result
    return wrapper

