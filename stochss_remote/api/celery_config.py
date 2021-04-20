redis_host = "localhost"
redis_port = 6379

broker_url = f"redis://{redis_host}:{redis_port}"
result_backend = f"redis://{redis_host}:{redis_port}"
result_extended = True