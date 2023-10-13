# Stream data from CSV

This project was created from the [RealTime From File](https://github.com/quixio/quix-samples/tree/main/python/sources/Real-Time-From-File) library item, modified
to read data from TSV instead of CSV and use one stream for each visitor UUID.

## Environment variables

The code sample uses the following environment variables:

- **output**: This is the output topic for realtime TSV data.
- **keep_timing**: '1' to stream data with original timing (only deltas), other value to stream data with a 0.2 second delay
