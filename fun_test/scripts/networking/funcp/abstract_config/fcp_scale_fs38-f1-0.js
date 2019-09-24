{
    "Description": "FS-38-F1-0 abstract cfg",
    "F1Index" : 1,
    "Interfaces" : [
	{ 
	    "name" : "fpg0", 
	    "address" : "13.1.1.1",
	    "prefix length" : 30,
	    "spine_index" : 0,
	    "gph_index" : 7,	    
	    "enable" : true
	},
        {
            "name" : "fpg4",
            "address" : "15.1.1.1",
            "prefix length" : 30,
            "spine_index" : 1,
            "gph_index" : 8,
            "enable" : true
        },
	{ 
	    "name" : "lo:0", 
	    "address" : "7.7.7.7",
	    "prefix length" : 32,	    
	    "enable" : true
	},
        {
            "name" : "vlan1",
            "address" : "71.1.1.1",
            "prefix length" : 24,
            "enable" : true
        }
    ],
    "BGP" : {
	"Local AS": 62002,
	"Neighbors" : [
	    { "peer" : "13.1.1.2", "peer-as": 62001},
	    { "peer" : "15.1.1.2", "peer-as": 62001}

	]
    }	
}
