# Aggregation service

This service reads data from the 'enrich data' topic, performs aggregations, and writes the results to Redis. These aggregations are then consumed by a Streamlit dashboard for visualization and analysis.

## Environment variables

The code sample uses the following environment variables:

- **input**: This is the input topic
- **redis_host**: This is the host for Redis
- **redis_port**: This is the port for Redis
- **redis_password**: This is the password for Redis


