import os
from datetime import datetime

import pandas as pd
import redis

r = redis.Redis(
    host=os.environ['redis_host'],
    port=os.environ['redis_port'],
    password=os.environ['redis_password'],
    decode_responses=True)


def load_products():
    products = pd.read_csv('products.tsv', sep='\t')
    for index, row in products.iterrows():
        key = f'product:{row["url"]}'
        r.hset(key, 'cat', row['category'])

    print(f"Imported {len(products)} products")


def load_users():
    users = pd.read_csv('users.tsv', sep='\t')
    total_users = len(users)
    imported_users = 0
    for index, row in users.iterrows():
        key = f'visitor:{row["SWID"]}'
        try:
            birthday = datetime.strptime(row['BIRTH_DT'], '%d-%b-%y')
            if birthday.year > 2005:
                birthday = birthday.replace(year=birthday.year - 100)

            r.hset(key, 'birthday', birthday.strftime('%Y-%m-%d'))
        except Exception as e:
            print("Cannot parse birthday: ", row['BIRTH_DT'], e)

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