# Variable to indicate the stage
export STAGE=dev

# Action server URL for Rasa chatbot within container
export ACTION_ENDPOINT=http://localhost:5055/webhook

# Universal Sentence Encoder config in TF Hub
export TFHUB_EMBEDDING_URL=https://tfhub.dev/google/universal-sentence-encoder/4
export TFHUB_CACHE_DIR=/var/tmp/tfhub_modules
export TF_CPP_MIN_LOG_LEVEL=3

# Elasticsearch settings
# export ES_IMITATE=false
export ES_IMITATE=true
export ELASTIC_USERNAME=elastic
export ELASTIC_PASSWORD=changeme
export ES_HOST=http://localhost:9200/

# Elasticseach indexes
export ES_ASKEXTENSION_INDEX=askextension
export ES_COMBINED_INDEX=combined