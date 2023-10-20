# Event Detection

This application is used to enrich the click data with the product category and the visitor gender, birthday and age.

This data is obtained from Redis, which is populated using other application.

## Environment variables

The code sample uses the following environment variables:

- **input**: This is the input topic for click stream
- **output**: This is the output topic for enriched data
- **redis_host**: This is the host for Redis
- **redis_port**: This is the port for Redis
- **redis_password**: This is the password for Redis
