#!/bin/bash
python -m scripts.async_download_data -c config.json
python -m scripts.merge_data -c config.json
python -m scripts.generate_features -c config.json
