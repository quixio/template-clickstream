import os
import pandas
import redis

r = redis.Redis(
  host=os.environ['redis_host'],
  port=os.environ['redis_port'],
  password=os.environ['redis_password'])