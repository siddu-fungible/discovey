# Integration
Integration testing infrastructure.

## Introduction
The Integration repository is organized as two major parts
1. fun_test (Containing regression infrastructure code, including scripts)
2. tools (Containing light-weight tools and Dockerfiles, which are not directly used by fun_test)

### fun_test
fun_test has the following layout
1. assets
2. system
3. scripts
4. scheduler
5. web

#### web
This is where the web-server, regression logs and database control modules are located.
The web-server operates in two modes, development mode and production mode (only used on the main regression server: integration.fungible.local)

##### Web-server in production mode
Refer: https://github.com/fungible-inc/Integration/blob/master/README-production-server.md

##### Web-server in development mode
