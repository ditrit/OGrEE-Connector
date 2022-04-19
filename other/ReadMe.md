# Notes for mini ETL connector


Quick Overview
------------
The most important file is the config.json which must be placed (and is included) in the same directory as the main.py script. This file contains the configuration for the import scripts. Please update this file before running any scripts.    

The default json files found in the defaultJSON folder are included and are used to provide default values for importing objects. These files are necessary for the import scripts.    


The json files found in the 'Template' folder contain the configuration for each object entity that describe how objects get imported into the OGREE DB and have a certain 'syntax' for describing as such. They are not required but are useful.    
    
    
Missing Objects
------------
In the event that objects are missing (ie no result for buildings or room has no corresponding building), the importer script will automatically insert the appropriate placeholder objects to satisfy the requirements of OGREE and continue with the import process.   



How to use import templates
------------
The import process works by using whatever values are present in the entity JSON, if a value is not present then it will not be used (unless it is necessary, which otherwise a default value will be used).    

For each field you may assign one of the following:
- same name as the field
- path string separated by quotes (ie 'attributes,customdict,color')
- description array

If you assign the same name as the field, the import script will refer and use the value directly found in the received json during the import process. For now the importer can only use the given value as a key (to index in the incoming json) directly.   

A path string separated by quotes describes how to index into the incoming object thus the field in question will be assigned the value found in the incoming object. For example 'color': 'attributes,customdict,color'. This means that the color field will be assigned as follows
```
 color = incomingObject['attributes']['customdict']['color']  
```

A description array allows you to describe the value that should be assigned. The first element in the array can one of 3 values:
- "manual"
- "default"
- "array" 

**Manual** tells the importer script to directly assign the 2nd element of the description array to the field.   
**Default** tells the importer script to use the value found in the default json.   
**Array** tells the importer script to assign an array and the 2nd element is a 'description dictionary'. This description dictionary describes the json of each element in the array. The values for the key fields can be 'manual', 'default' or path based string. For the path based string (which is most likely what would be used for elements in this array), you can use the 'iter' keyword to indicate that the path in the incoming object should be indexed the same way numerically as the array to be generated (ie incomingObject['attr'][#] -> newJSON['attr'][#]) 