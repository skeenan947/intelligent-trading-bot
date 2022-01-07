#!/bin/bash
gsutil -m cp  -r gs://sk-trading-bot/data-btc-fullhistory/ .
mv data-btc-fullhistory data
gsutil -m cp -r gs://sk-trading-bot/model-btc-fullhistory/ .
mv model-btc-fullhistory model
