//
//  utils.h
//
//  Created by Bertrand Serlet on 7/14/20.
//  Copyright © 2017 Fungible. All rights reserved.
//

#pragma once

// This file is intended to include very common utilities, like syslog()
// We should be very picky about what get included here
// to avoid extending the dependency graph.

//#include "macros.h"
//#include "syslog.h"
#define SYSLOG(_hu_f, _severity, _facility, _fmt, ...) \
        printf(_fmt, ##__VA_ARGS__);\
        printf("\n\n");
