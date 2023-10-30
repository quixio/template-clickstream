#!/bin/sh

# Create or update the Angular environment file (environment.prod.ts)
echo "export const environment = {" > /environments/environment.prod.ts
echo "  isProduction: true," >> /environments/environment.prod.ts
echo "  TOKEN: '${bearer_token}'," >> /environments/environment.prod.ts
echo "  WORKSPACE_ID: '${Quix__Workspace__Id}'," >> /environments/environment.prod.ts
echo "  CLICK_TOPIC: '${click_topic}'," >> /environments/environment.prod.ts
echo "  OFFERS_TOPIC: '${offers_topic}'," >> /environments/environment.prod.ts
echo "  DEPLOYMENT_ID: '${Deployment__Id}'" >> /environments/environment.prod.ts
echo "};" >> /environments/environment.prod.ts

# Print the contents of environment.prod.ts to the console
cat /environments/environment.prod.ts


# Start the NGINX server
nginx -g "daemon off;"
