REDIS_HOST = "redis"
REDIS_PORT = 6379

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}"
result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}"
result_extended = True