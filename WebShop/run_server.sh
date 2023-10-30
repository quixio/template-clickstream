#!/bin/sh
# generate .env.prod with required values
echo "bearer_token=${bearer_token}" > /usr/share/nginx/html/.env.prod
echo "Quix__Workspace__Id=${Quix__Workspace__Id}" >> /usr/share/nginx/html/.env.prod
echo "Quix__Portal__Api=${Quix__Portal__Api}" >> /usr/share/nginx/html/.env.prod
echo "click_topic=${click_topic}" >> /usr/share/nginx/html/.env.prod
echo "offers_topic=${offers_topic}" >> /usr/share/nginx/html/.env.prod
nginx -g "daemon off;"
