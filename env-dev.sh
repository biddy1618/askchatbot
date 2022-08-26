# Action server URL for Rasa chatbot within container
export ACTION_ENDPOINT=http://localhost:5055/webhook

# Rasa SpaCy models variables
export TOKENIZERS_PARALLELISM=false

# Universal Sentence Encoder config in TF Hub
export TF_CPP_MIN_LOG_LEVEL=3
export TFHUB_CACHE_DIR=/var/tmp/models

# Elasticsearch settings
export ELASTIC_USERNAME=elastic
export ELASTIC_PASSWORD=changeme
export ES_HOST=http://localhost:9200/
