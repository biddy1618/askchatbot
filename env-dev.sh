

# Variable to indicate the stage
export STAGE=dev
export DEPLOYMENT_VERSION=04.04.22

# Variables for Rasa configuration
export DEBUG=true
export ES_SEARCH_SIZE=100
export ES_CUT_OFF=0.4
export ES_TOP_N=5
export ES_ASK_WEIGHT=0.6

# Action server URL for Rasa chatbot within container
export ACTION_ENDPOINT=http://localhost:5055/webhook

# Rasa SpaCy models variables
export TOKENIZERS_PARALLELISM=false

# Universal Sentence Encoder config in TF Hub
export TFHUB_EMBEDDING_URL=https://tfhub.dev/google/universal-sentence-encoder/4
export TFHUB_CACHE_DIR=/var/tmp/tfhub_modules
export TF_CPP_MIN_LOG_LEVEL=3

# Elasticsearch settings
export ES_IMITATE=false
# export ES_IMITATE=true
export ELASTIC_USERNAME=elastic
export ELASTIC_PASSWORD=changeme
export ES_HOST=http://localhost:9200/

# Elasticseach indexes
export ES_ASKEXTENSION_INDEX=askextension
export ES_COMBINED_INDEX=combined