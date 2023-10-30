#!/bin/sh


# /usr/share/nginx/html
pwd




# Print the contents of environment.prod.ts to the console
cat /app/src/environments/environment.prod1.ts

# Create or update the Angular environment file (environment.prod.ts)
echo "export const environment = {" > /app/src/environments/environment.prod1.ts
echo "  isProduction: true," >> /app/src/environments/environment.prod1.ts
echo "  TOKEN: '${bearer_token}'," >> /app/src/environments/environment.prod1.ts
echo "  WORKSPACE_ID: '${Quix__Workspace__Id}'," >> /app/src/environments/environment.prod1.ts
echo "  CLICK_TOPIC: '${click_topic}'," >> /app/src/environments/environment.prod1.ts
echo "  OFFERS_TOPIC: '${offers_topic}'," >> /app/src/environments/environment.prod1.ts
echo "  DEPLOYMENT_ID: '${Deployment__Id}'" >> /app/src/environments/environment.prod1.ts
echo "};" >> /app/src/environments/environment.prod1.ts

# Print the contents of environment.prod.ts to the console
cat /app/src/environments/environment.prod1.ts


# Start the NGINX server
nginx -g "daemon off;"
