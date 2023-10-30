#!/bin/sh

# Check if 'ls' is available
command -v ls >/dev/null 2>&1 || { echo >&2 "ls is required but not found. Aborting."; exit 1; }


# List files and folders in the current working directory
ls

# Print the contents of environment.prod.ts to the console
cat /app/src/environments/environment.prod.ts

# Create or update the Angular environment file (environment.prod.ts)
echo "export const environment = {" > /app/src/environments/environment.prod.ts
echo "  isProduction: true," >> /app/src/environments/environment.prod.ts
echo "  TOKEN: '${bearer_token}'," >> /app/src/environments/environment.prod.ts
echo "  WORKSPACE_ID: '${Quix__Workspace__Id}'," >> /app/src/environments/environment.prod.ts
echo "  CLICK_TOPIC: '${click_topic}'," >> /app/src/environments/environment.prod.ts
echo "  OFFERS_TOPIC: '${offers_topic}'," >> /app/src/environments/environment.prod.ts
echo "  DEPLOYMENT_ID: '${Deployment__Id}'" >> /app/src/environments/environment.prod.ts
echo "};" >> /app/src/environments/environment.prod.ts

# Print the contents of environment.prod.ts to the console
cat /app/src/environments/environment.prod.ts