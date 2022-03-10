# UC IPM Data

## Data retrieval

Data can be obtained through DVC ([installation guide](https://wiki.eduworks.com/Information_Technology/MLOps/DATA-Installing-DVC)). Clone the [repository](https://git.eduworks.us/data/ask-extension/uc-ipm-web-scrape) for scraped data, install Google Cloud Client - `gcloud` (more in installation guide), authenticate, and pull the data through dvc. Please, contact admin for access rights.


### ETL and EDA

More information can be found in `./scripts/eda_ipmdata.ipynb` notebook.

### Final mappings

`Problem` index:
```json
{
    "source"        : "pestsIPM/pestsDiseases/pestsTurf/pestsExotic/damagesEnvironment/damagesWeed",
    "name"          : "text",
    "url"           : "url",
    "description"   : "text",
    "identification": "text",
    "development"   : "text",
    "damage"        : "text",
    "management"    : "text",
    "links": [
        {
            "type"      : "images/video/page",
            "caption"   : "...",
            "src"       : "urlSource",
            "link"      : "urlAdditional"
        },
        ...
    ],
}
```

`Information` index:
```json
{
        "source"        : "fruits/veggies/flowers",
        "name"          : "text",
        "url"           : "url",
        "description"   : "description",
        "management"    : "management",
        "links": [
            {
                "type"  : "tips/images",
                "src"   : "urlSource",
                "link"  : "urlAdditional"
            },
            ...
        ],
        "problems": [
            {
                "problem"   : "text",
                "src"       : "url"
            },
            ...
        ]
    },
```
## Universal Sentence Encoder

Original [paper](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/46808.pdf) about universal sentence encoder.

## Notes

* [Single vector field](https://stackoverflow.com/questions/61376317/dense-vector-array-and-cosine-similarity) as mapping and corresponding query for that.