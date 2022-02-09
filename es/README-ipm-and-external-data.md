# UC IPM Data

## Data retrieval

Data can be obtained through DVC ([installation guide](https://wiki.eduworks.com/Information_Technology/MLOps/DATA-Installing-DVC)). Clone the [repository](https://git.eduworks.us/data/ask-extension/uc-ipm-web-scrape) for scraped data, install Google Cloud Client - `gcloud` (more in installation guide), authenticate, and pull the data through dvc. Please, contact admin for access rights.

## IPM Data - `ipmdata_new.json`

| column              | type                                  |
|---------------------|---------------------------------------|
| name                | string                                |
| urlPestNote         | string                                |
| descriptionPestNote | string                                |
| life_cycle          | string                                |
| damagePestNote      | string                                |
| managementPestNote  | string                                |
| imagePestNote       | [{link: " ", src: " ", caption: " "}] |
| tablePestNote       | [" ", " "]                            |
| urlQuickTip         | string                                |
| contentQuickTips    | string                                |
| imageQuickTips      | [{link: " ", src: " ", caption: " "}] |
| video               | [{videoLink: " ", videoTitle: " "}]   |

## Fruits - `fruitItems_new.json`

| column              | type                      |
|---------------------|---------------------------|
| name                | string                    |
| url                 | string                    |
| cultural_tips       | [{tip: "", link: ""}]     |
| pests_and_disorders | [{problem: "", link: ""}] |

## Veggie - `veggieItems_new.json`

| column              | type                                  |
|---------------------|---------------------------------------|
| name                | string                                |
| url                 | string                                |
| description         | string                                |
| tips                | string                                |
| images              | [{link: " ", src: " ", caption: " "}] |
| pests_and_disorders | [{problem: "", link: ""}]             |

## Environment Fruit and Veggie - `fruitVeggieEnvironItems_new.json`

| column               | type                                  |
|----------------------|---------------------------------------|
| name                 | string                                |
| url                  | string                                |
| description          | string                                |
| identification       | string                                |
| damage               | string                                |
| disorder_development | string                                |
| solutions            | string                                |
| images               | [{link: " ", src: " ", caption: " "}] |

## Flowers - `plantFlowerItems.json`

| column              | type                        |
|---------------------|-----------------------------|
| name                | string                      |
| url                 | string                      |
| identification      | string                      |
| optimum_conditions  | string                      |
| pests_and_disorders | [{problem: " ", link: " "}] |

## Weed - `weedItems.json`

| column      | type                        |
|-------------|-----------------------------|
| name        | string                      |
| url         | string                      |
| description | string                      |
| images      | [{link: " ", caption: " "}] |

## Pest Diseases - `pestDiseasesItems_new.json`

| column         | type                                  |
|----------------|---------------------------------------|
| name           | string                                |
| url            | string                                |
| description    | string                                |
| identification | string                                |
| life_cycle     | string                                |
| damage         | string                                |
| solutions      | string                                |
| images         | [{link: " ", src: " ", caption: " "}] |

## Exotic pests - `exoticPests.json`

| column         | type                     |
|----------------|--------------------------|
| name           | string                   |
| url            | string                   |
| description    | string                   |
| damage         | string                   |
| identification | string                   |
| life_cycle     | string                   |
| monitoring     | string                   |
| management     | string                   |
| related_links  | [{text: " ", link: " "}] |

## Turf Pests - `turfPests.json`

| column | type                                  |
|--------|---------------------------------------|
| name   | string                                |
| url    | string                                |
| text   | string                                |
| images | [{link: " ", src: " ", caption: " "}] |

