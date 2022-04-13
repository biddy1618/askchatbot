# New entities mapping logic

## New entities

Entities:
* action
* descr
* location
* name
* part (can have only plant and pest as a role)
* type (can have only plant and pest as a role)

Roles:
* pest
* plant
* damage


Groups:
* from 1 to n

## Mapping logic

Order:
1. Groups
2. Roles
    1. Pest
    2. Damage
    3. Plant
3. Entities:
    1. descr
    2. (type |) name (| part)
    3. action
    4. location

## Slot strucure

```JavaScript
{
    // Group keys
    Group1:
    {
        // Role keys with ordered tuples of entities
        pest    : [(order, entity_name, entity_value), ...],
        damage  : [(order, entity_name, entity_value), ...],
        plant   : [(order, entity_name, entity_value), ...]
    },
    ...,
    GroupN: ...
}
```