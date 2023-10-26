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
    for index, row in products.iterrows():
        key = f'product:{row["id"]}'
        r.hset(key, 'cat', row['category'])
        r.hset(key, 'title', row['title'])

    print(f"Imported {len(products)} products")


# Read visitor data from users.tsv and store gender, birthday and age in Redis
def load_users():
    users = pd.read_json('users.json', lines=True)
    total_users = len(users)
    imported_users = 0
    for _, row in users.iterrows():
        key = f'visitor:{row["userId"]}'

        # Birthday may not be present, check for NaN
        if not pd.isna(row['birthDate']):
            r.hset(key, 'birthday', row['birthDate'])

        # Age may not be present, check for NaN
        if not pd.isna(row['gender']):
            r.hset(key, 'gender', row['gender'])

        imported_users += 1

        if imported_users % 100 == 0:
            print(f"Imported {imported_users} of {total_users} users")


def main():
    print("Importing products...")
    load_products()

    print("Importing users...")
    load_users()

    # Do some assertions to make sure the data is loaded correctly
    print("Checking data...")
    if r.hget("product:VR55181666", "cat") != "handbags":
        raise Exception("Wrong category for product")

    if r.hget("visitor:001BFE35-555B-48E1-9ED3-A4BE7677C36C", "birthday") != "1982-02-16":
        raise Exception("Wrong birthday for user")


if __name__ == '__main__':
    main()
