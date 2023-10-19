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
    products = pd.read_json('products.json', lines=True)
    for index, row in products.iterrows():
        key = f'product:{row["url"]}'
        r.hset(key, 'cat', row['category'])
        r.hset(key, 'title', row['title'])

    print(f"Imported {len(products)} products")


# Read visitor data from users.tsv and store gender, birthday and age in Redis
def load_users():
    users = pd.read_json('users.json', lines=True)
    total_users = len(users)
    imported_users = 0
    for _, row in users.iterrows():
        key = f'visitor:{row["SWID"]}'

        # Birthday may not be present, check for NaN
        if not pd.isna(row['BIRTH_DT']):
            birthday = datetime.strptime(row['BIRTH_DT'], '%d-%b-%y')
            if birthday.year > 2005:
                birthday = birthday.replace(year=birthday.year - 100)

            r.hset(key, 'birthday', birthday.strftime('%Y-%m-%d'))

        # Age may not be present, check for NaN
        if not pd.isna(row['GENDER_CD']):
            r.hset(key, 'gender', row['GENDER_CD'])

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
    if r.hget("product:http://www.acme.com/SH5584743/VD55162989", "cat") != "grocery":
        raise Exception("Wrong category for product")

    if r.hget("visitor:0044AF02-16EC-42B0-96DD-52679773A9D6", "birthday") != "2006-07-17":
        raise Exception("Wrong birthday for user")


if __name__ == '__main__':
    main()