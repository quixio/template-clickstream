import os
from datetime import datetime

import pandas as pd
import redis

r = redis.Redis(
    host=os.environ['redis_host'],
    port=os.environ['redis_port'],
    password=os.environ['redis_password'],
    decode_responses=True)


# Read products from products.tsv and store the category in Redis
def load_products():
    products = pd.read_json('products.json')
    pipe = r.pipeline()

    for index, row in products.iterrows():
        key = f'product:{row["id"]}'
        pipe.hmset(key, {'cat': row['category'], 'title': row['title']})

    pipe.execute()
    print(f"Imported {len(products)} products")


# Read visitor data from users.tsv and store gender, birthday and age in Redis
def load_users():
    users = pd.read_json('users.json', lines=True)
    total_users = len(users)
    imported_users = 0
    pipe = r.pipeline()
    for _, row in users.iterrows():
        key = f'visitor:{row["userId"]}'
        values = {}

        # Birthday may not be present, check for NaN
        if not pd.isna(row['birthDate']):
            values['birthday'] = row['birthDate']

        # Age may not be present, check for NaN
        if not pd.isna(row['gender']):
            values['gender'] = row['gender']

        pipe.hmset(key, values)
        imported_users += 1

        if imported_users % 100 == 0:
            pipe.execute()
            print(f"Imported {imported_users} of {total_users} users")

    # Last execute to flush the pipeline
    pipe.execute()

def main():
    print("Importing products...")
    load_products()

    print("Importing users...")
    load_users()



if __name__ == '__main__':
    main()
