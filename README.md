# Verifiedpixel
*Version 0.1*
Documentation (Coming soon) •
## Requirements
* node.js
* python
* mongodb
* elasticsearch
* redis

## Build the server
For the sake of simplification we're going to say that you're in your download location.
```bash
$cd server
$virtualenv env
$source env/bin/activate
(env)$pip install -r requirements.txt
```
You will need your API keys to hand, Tineye, Izitru, and Google Reverse Image Search. We advise you bundle them into a file and just hit them all at once but here is what you will need:
```bash
export TINEYE_PUBLIC_KEY="<API PUBLIC KEY>" 
export TINEYE_SECRET_KEY="<API SECRET KEY>"

export IZITRU_PRIVATE_KEY="<IZITRU PRIVATE KEY>"
export IZITRU_ACTIVATION_KEY="<IZITRU ACTIVATION KEY>"

export GRIS_API_KEY="<GRIS API KEY>"
export GRIS_API_CX="<GRIS API CX>"
```
If you've made your keys into a script into an executable (chmod a+x) execute it with:
```bash
(env)$source yourscriptname
```
## Build the client
Open a new terminal pane.
```bash
$cd client
$sudo npm install
$bower install
$grunt server
```
Start your redis, elasticearch, and mongodb services. Start the application.
```bash
(env)$honcho start
```