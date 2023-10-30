#!/bin/sh
# generate .env.prod with required values
echo "bearer_token=${bearer_token}" > /environments/.env.prod
echo "Quix__Workspace__Id=${Quix__Workspace__Id}" >> /environments/.env.prod
echo "Quix__Portal__Api=${Quix__Portal__Api}" >> /environments/.env.prod
echo "click_topic=${click_topic}" >> /environments/.env.prod
echo "offers_topic=${offers_topic}" >> /environments/.env.prod
nginx -g "daemon off;"
