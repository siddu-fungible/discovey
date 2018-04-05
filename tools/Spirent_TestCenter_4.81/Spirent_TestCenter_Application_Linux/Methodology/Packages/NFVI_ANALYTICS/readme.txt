Gayan 10/6/17:

- The methodology has no STC ports. The export wizard allows this.

- To use the meth export wizard, a property must be exposed. As a workaround I exported CreateDefaultNfviRealTimeResults and manually removed the "property_groups" list from the meta.json after exporting. It would be good to update the export wizard so a parameter is not required.

- In the interactive.json "rt_results" section, I copied the JSON from the init_nfvi_results.json file. We should be able to specify an init file instead of only JSON in interactive.json .
