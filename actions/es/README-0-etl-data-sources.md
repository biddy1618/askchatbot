# UC IPM Data

### ETL and EDA

More information can be found in `./scripts/es_etl.ipynb` notebook.

### Final mappings

`Dec2021` scrape:
```json
{
    "source"        : "pestsIPM/pestsDiseases/pestsTurf/pestsExotic/damagesEnvironment/damagesWeed/infoFruits/infoVeggies/infoFlowers",
    "name"          : "text",
    "url"           : "url",
    "description"   : "text",
    "identification": "text",
    "development"   : "text",
    "damage"        : "text",
    "management"    : "text",
    "links": [
        {
            "type"      : "image/video/page",
            "title"     : "...",
            "src"       : "urlSource",
            "link"      : "urlAdditional"
        },
        ...
    ],
}
```

`Apr2021` scrape:
```json
{
    "source"        : "infoFruitVegCultural/infoPestControl/infoPesticideControl/pestsNotes/pestsQuickTips/pestsVideos/pestsWeed",
    "name"          : "text",
    "url"           : "url",
    "description"   : "text",
    "development"   : "text",
    "damage"        : "text",
    "links": [
        {
            "type"      : "images",
            "title"     : "...",
            "src"       : "urlSource",
            "link"      : "urlAdditional"
        },
        ...
    ]
}
```
## Universal Sentence Encoder

Original [paper](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/46808.pdf) about universal sentence encoder.

## Notes

* [Single vector field](https://stackoverflow.com/questions/61376317/dense-vector-array-and-cosine-similarity) as mapping and corresponding query for that.



# AskExtension Knowledge Base data

## API for retrieving data

Data can be retrieved through this API `https://ask2.extension.org/api/knowledge/YYYY-MM-DD/YYYY-MM-DD` like so:
```bash
curl https://ask2.extension.org/api/knowledge/2012-12-05/2012-12-06
```
where first date indicates start date and second date indicates end date (both inclusive).

## Data description

Ask Extension data obtained through API looks the following way:
```
[
  {
    "faq-id": 1,
    "title": "When can I plant blue spruce trees in Colorado? #109900",
    "created": "2012-12-03 15:53:47",
    "updated": "2012-12-03 17:47:21",
    "tags": ["trees and shrubs"],
    "state": "Colorado",
    "county": "El Paso County",
    "question": "I need to plant two blue spruce trees that are currently in 24\" diameter plastic containers with drain holes in the bottom sides.\n\nLocation: northeast side of Colorado Springs.\n\nThese trees are currently outside on the patio and susceptible to the wind and sun. The trees were watered this past Saturday and seem to be healthy.\n\nQuestion: Can these trees be planted now? Currently the soil is not frozen and night time temps are 35 to 40 degrees.\n\nI have downloaded and read CMG GardenNotes #633 as a reference.\n\nAny advice would be greatly appreciated. ",
    "answer": {
      "1": {
        "response": "Jerry, \nyou can plant them now (a) OR temporarily \"plant\" them, still in containers, so that roots have some insulation from cold (b).\n\n(a) if you know where you want these trees to be planted (check for overhead utility lines AND for underground utility lines before digging by calling 8-1-1), dig holes 2-3X as wide as rootball and as deep as the rootball or slightly shallower.  To excavated soil, add organic matter (compost, shhagnum peat, etc) at 20% by volume.  Mix thoroughly to homogenize.    \nInspect rootball for circling roots and tease them out of circling pattern if possible.   Plant tree so that top of rootball is at or a couple inches above grade.   Backfill with amended excavated soil.  Water well and add more soil where settling occurs.\nMulch planting area with 2-3 inches of wood chips or similar mulch.   Water again to settle mulch.    Water again in a week and continue watering weekly until there is cold and snowcover.  Water again if weather warms, snowcover  melts and soils begin to dry out.\n\n(b) to \"store\" potted spruces temporarily in soil area (N or E exposure better than S or W), dig holes 1.5X as wide and same depth as rootball. Sink pots into holes and backfill.  Mulch surface of rootball in pot with straw or woodchips.   Water rootballs in pots and repeat whenever weather has been warm and there is no snowcover.   Plant spruces in permanent spot next April as per (a) above.",
        "author": "Robert Cox"
      }
    }
  },
  ...
```

It is a list of dictionary objects with following fields:
- `faq-id` - ID of the ticket
- `title` - title of the ticket along ID of the ticket (other ID)
- `created` - ticket creating date
- `updated` - ticket last update date
- `tags` - list of tags
- `state` - state ticket was created in
- `county` - county ticket was created in
- `question` - question that has been posted
- `answer` - responselists presented in numbered dictionary data type

### Final mappings

```json
{
    "source"        : "askExtension",
    "name"          : "text",           # title
    "url"           : "url",            # url
    "description"   : "text",           # title_question
    "links": [
        {
            "type"      : "tag/answer",
            "title"     : "...",
            "src"       : "urlSource",
            "link"      : "urlAdditional"
        },
        ...
    ]
}
```

### ETL and EDA

More information can be found in `./scripts/es_etl.ipynb` notebook.

## Person of contact

For details, contact [Autunm Greenley](autumn.greenley@eduworks.com).