import time

def retry_handler(max_retry = 5, sleep_time = 0.5):
    def decorator(function):
        def inner_function(*args, **kwargs):
            attempt = 0
            while attempt < max_retry:
                try:
                    return function(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                time.sleep(sleep_time * attempt)
            if attempt >= max_retry:
                raise TimeoutException
            return function(*args, **kwargs)

        return inner_function

    return decorator

class TimeoutException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return "exceeded the retry_timeout"