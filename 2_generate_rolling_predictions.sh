#!/bin/bash
python -m scripts.generate_rolling_predictions -c config.json
gsutil cp -r model gs://sk-training-bot/model-predictions
