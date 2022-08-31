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

# Should be simplified later. Lots of timeout settings in RASA and multiple seem to trigger timeout errors for longer actions
export STREAM_READING_TIME_ENV=300
export SANIC_REQUEST_TIMEOUT=300
export REQUEST_TIMEOUT=300
export RESPONSE_TIMEOUT=300
export DEFAULT_STREAM_READING_TIMEOUT_IN_SECONDS=120
