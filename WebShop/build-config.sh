# List files and folders in the current working directory
ls

# Print the contents of environment.prod.ts to the console
cat /src/environments/environment.prod.ts

# Create or update the Angular environment file (environment.prod.ts)
echo "export const environment = {" > /src/environments/environment.prod.ts
echo "  isProduction: true," >> /src/environments/environment.prod.ts
echo "  TOKEN: '${bearer_token}'," >> /src/environments/environment.prod.ts
echo "  WORKSPACE_ID: '${Quix__Workspace__Id}'," >> /src/environments/environment.prod.ts
echo "  CLICK_TOPIC: '${click_topic}'," >> /src/environments/environment.prod.ts
echo "  OFFERS_TOPIC: '${offers_topic}'," >> /src/environments/environment.prod.ts
echo "  DEPLOYMENT_ID: '${Deployment__Id}'" >> /src/environments/environment.prod.ts
echo "};" >> /src/environments/environment.prod.ts

# Print the contents of environment.prod.ts to the console
cat /src/environments/environment.prod.ts