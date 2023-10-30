#!/bin/sh
# generate .env.prod with required values
echo "bearer_token=${bearer_token}" > /environments/.environment.prod.ts
echo "Quix__Workspace__Id=${Quix__Workspace__Id}" >> /environments/.environment.prod.ts
echo "Quix__Portal__Api=${Quix__Portal__Api}" >> /environments/.environment.prod.ts
echo "click_topic=${click_topic}" >> /environments/.environment.prod.ts
echo "offers_topic=${offers_topic}" >> /environments/.environment.prod.ts
nginx -g "daemon off;"
