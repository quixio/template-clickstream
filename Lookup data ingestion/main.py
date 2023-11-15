import os
import pandas as pd
import redis

r = redis.Redis(
    host=os.environ['redis_host'],
    port=int(os.environ['redis_port']),
    password=os.environ['redis_password'],
    username=os.environ['redis_username'] if 'redis_username' in os.environ else None,
    decode_responses=True)


# Read products from products.tsv and store the category in Redis
def load_products():
    products = pd.read_json('products.json')
    pipe = r.pipeline()

    for index, row in products.iterrows():
        key = f'product:{row["id"]}'
        pipe.hset(key, 'cat', row['category'])
        pipe.hset(key, 'title', row['title'])

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

        # Birthday may not be present, check for NaN
        if not pd.isna(row['birthDate']):
            pipe.hset(key, 'birthday', row['birthDate'])

        # Age may not be present, check for NaN
        if not pd.isna(row['gender']):
            pipe.hset(key, 'gender', row['gender'])

        imported_users += 1

        if imported_users % 1000 == 0:
            pipe.execute()
            print(f"Imported {imported_users} of {total_users} users")

    # Last execute to flush the pipeline
    pipe.execute()
    print(f"Imported all {total_users} users")


def main():
    print("Importing products...")
    load_products()

    print("Importing users...")
    load_users()


if __name__ == '__main__':
    main()
