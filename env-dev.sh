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

# Work around for longer actions: 
export STREAM_READING_TIMEOUT_ENV= 5000
export SANIC_RESPONSE_TIMEOUT= 28800
export SANIC_REQUEST_TIMEOUT= 5000
export REQUEST_TIMEOUT= 3600