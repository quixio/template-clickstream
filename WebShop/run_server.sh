#!/bin/sh

# Create or update the Angular environment file (environment.prod.ts)
echo "export const environment = {" > /usr/share/nginx/html/environment.prod.ts
echo "  isProduction: true," >> /usr/share/nginx/html/environment.prod.ts
echo "  TOKEN: '${bearer_token}'," >> /usr/share/nginx/html/environment.prod.ts
echo "  WORKSPACE_ID: '${Quix__Workspace__Id}'," >> /usr/share/nginx/html/environment.prod.ts
echo "  CLICK_TOPIC: '${click_topic}'," >> /usr/share/nginx/html/environment.prod.ts
echo "  OFFERS_TOPIC: '${offers_topic}'," >> /usr/share/nginx/html/environment.prod.ts
echo "  DEPLOYMENT_ID: '${Deployment__Id}'" >> /usr/share/nginx/html/environment.prod.ts
echo "};" >> /usr/share/nginx/html/environment.prod.ts

# Start the NGINX server
nginx -g "daemon off;"
