# Detect User Behaviour

This project is to detect user behaviour in real-time.

The class `UserBehaviour` is used to detect the user behaviour. If the user clicks on the same product category more 
than 3 times in 30 minutes, then we launch an offer.

The logic is implemented in the `process_dataframe` method, and first of all cleans data to avoid storing
unnecessary data in memory (cleans page refreshes and ignores all actions that are not considered for the offers).
Then, it checks if the click is eligible for an offer, and if we detect that the user clicked 3 times on this
kind of product, we launch an offer.

## Environment variables

The code sample uses the following environment variables:
- **input**: This is the input topic for click stream
- **window_minutes**: This is the window in minutes to consider for the user behaviour


