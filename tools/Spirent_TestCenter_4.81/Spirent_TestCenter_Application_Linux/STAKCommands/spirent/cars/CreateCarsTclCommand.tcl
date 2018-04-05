proc validate {NumCars} {
    # Nothing to validate in this case. Framework is validating the numeric restriction. 
    return ""
}


# Creates n number of cars and sets the Cars output property.  
proc run {NumCars} {                            
    # Get the 1 and only project.
    set project [ stc::get system1 -children-project ]
    
    # Create a command and Execute
    array set out [ stc::perform CreatorCommand -CreateClassId car -CreateCount $NumCars -ParentList $project ]    

    # Get the handle list to set the output property Cars and log a message.
    set carHandles $out(-ReturnList)
    stc::log INFO "[ llength $carHandles ] cars were created."

    global __commandHandle__
    stc::config $__commandHandle__ -Status "CreateCarsCommand completed sucessfully!"
    stc::config $__commandHandle__ -Cars $carHandles            
    return 1
}

proc reset {} {
    # Reset any state needed to run the command again, i.e. delete temp files, 
    # modify object model state, etc. 
    return 1
}

