#!/bin/bash
export TF_CPP_MIN_LOG_LEVEL=3
python -m scripts.generate_rolling_predictions -c config.json
gsutil -m cp -r model gs://sk-trading-bot/model-predictions
gsutil -m cp -Zr data gs://sk-trading-bot/data-predictions
