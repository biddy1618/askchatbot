# [UC IPM]([Integrated Pest Management](http://ipm.ucanr.edu/)) - [Pest Notes](http://ipm.ucanr.edu/PMG/PESTNOTES/index.html)

### How to scrape the data for use by the chatbot

Initial investigation of the web pages:

- The [List of pest notes](http://ipm.ucanr.edu/PMG/PESTNOTES/index.html) contains URLs to the actual pest notes
- Inspection of a few pest notes shows a consistent structure with these sections:
  - `Pest Name` at this XPATH: <----->
  - `Pest Description`  at this XPATH:  <----->
  - `Pest Identification`  at this XPATH:  <----->
  - `Pest Damage`  at this XPATH:  <----->
  - `Pest Management`  at this XPATH:  <----->

Because the Pest Notes are very structured, it should work to use [scrapy](https://scrapy.org/) to extract this content of and inject it all into an intermediate Database & also into ElasticSearch.



### How to use the information of the Pest Notes

##### <u>Initial implementation: Use the `Pest Name, Description, Identification & Damage`</u> 

1. Ask user for a description of the pest problem
2. Find *'closest match'* to the Pest Name, Description, Identification & Damage sections of the pest notes
   - Option 1: Query Elasticsearch
   - Option 2: Query a custom build machine learning model
3. Provide the pest note URL of this closest match back to the user
4. Ask user:
   - If the pest was properly identified
     - If Yes: if the information provided was helpful
   - Any other suggestions or feedback?

##### <u>Improvement: ask for more specific pest identification details</u>

Based on the most commonly asked about pests, for example ants, a more detailed Form can be implemented to ask more specific pest identification questions that will improve predictive performance of the Query.  



# Example Questions from the [legacy system](https://ask.extension.org/) 

Note: Most of these questions include images.

These are about pests:

| Title & URL                                              | Question                                                     | Answer (URL)                                                 | Entities                                         |
| -------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------ |
| [Worms](https://ask.extension.org/questions/464882):     | I found this cluster of worms(?) on a bike path in a wooded area and am  curious about what they are. The total length of the cluster is about 5  inches.  I have included two pictures. | [fungus-gnats - UMD](https://extension.umd.edu/hgic/topics/fungus-gnats) | pest_type=worms; pest_size=5; pest_size_unit=in; |
| [Fruitflies](https://ask.extension.org/questions/615951) | Client has been dealing with very small, delicate flies that resemble  fruit flies that come from her indoor plants. She wonders if the issue  came from moving the plants from outdoors to indoors or from re-potting  them. The insects aren't afraid to land on any surface, including in  liquids or on your face. They're slow and she is able to catch them with ease. We did some looking and found fungus gnats to be an option, but  these insects are quite smaller than a mosquito--what was used to  identify the size of fungus gnats. I've attached a few photos of the  insects she bagged and included a small paperclip for size comparison. | [fungus-gnats - Michigan State](https://www.canr.msu.edu/resources/fungus-gnats) |                                                  |
| [gnats](https://ask.extension.org/questions/632943)      | We have a ton of gnats that are gathering indoors in one window and dying there. What should we do? | [fungus-gnats - CSU](https://extension.colostate.edu/topic-areas/insects/fungus-gnats-as-houseplant-and-indoor-pests-5-584/) |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |
|                                                          |                                                              |                                                              |                                                  |

These are not about pests:
- https://ask.extension.org/questions/635367 
- https://ask.extension.org/questions/635366



It is not clear yet how we could use this data for the chatbot.