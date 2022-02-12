ASKEXTENSION = {
    "settings": {
        "number_of_shards": 1
    },
    "mappings": {
        "properties": {
            "faq-id": {"type": "integer"},
            "ticket-no": {"type": "text"},
            "url": {"type": "text"},
            "created": {"type": "text"},
            "updated": {"type": "text"},
            "state": {"type": "text"},
            "county": {"type": "text"},
            "title": {"type": "text"},
            "question": {"type": "text"},
            "title-question": {"type": "text"},
            "answer": {"type": "text"},
        }
    }
}