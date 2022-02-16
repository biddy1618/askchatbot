# Design document

## Initial scetches

For the first iteration, we are going to address the following parts:

- Cultural tips. Entities: `plant_type`, `plant_name`, `tip_formulation`
    - Question
- Plant problem. Entities: `plant_type`, `plant_name`, `problem_description`, `plant_damage`, `general_question`, `pest_name`, `problem_name`
    - Pest problem
    - Disease problem
    - Description
- 


1. Plant problem
2. Disease and pests

In order to accomplish that we need to build some form of possible tree to address the issues of the user. THE MOST FUNDAMENTAL PART in my opinion is the plant itself in resolving this question. Since pests and diseases can be subject to plant type, the foremost question that we need to ask is the plant type and name.

1. What kind of plant do you have?
2. If you are aware the plant name, can you type it?
3. Part of the plant that is damaged?
4. Description of the damage.

Other questions to ask:
* Did you find bug and send the image?
* Is there something wrong with plant?
* Part of the plant?


Things to do:

1. Parse the docs using Python to retrive the families of the plants, names of the plants, parts damaged, description, and for the second document retrieve the matrix of the damages and possible pests that might be causing it.