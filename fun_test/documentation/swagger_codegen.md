# Creating Python SDK using swagger documentation

This document explains how to use Swagger Documentation to create a Python SDK from it.
We need to create a new Python SDK everytime there is a change in the Fungible(storage) controller API definition and 
the Swagger Documentation.

## Installing the Swagger Codegen

### Linux

We can use a Java .jar file to create SDK

```
wget https://repo1.maven.org/maven2/io/swagger/swagger-codegen-cli/2.4.12/swagger-codegen-cli-2.4.12.jar -O swagger-codegen-cli.jar

java -jar swagger-codegen-cli.jar help
```

### Mac
Mac Users need to have Java 8+

```
brew install swagger-codegen
swagger-codegen help
swagger-codegen generate help
```

## Generating the Swagger SDK

```
java -jar swagger-codegen-cli.jar generate -i /tmp/swagger.yaml -l python -o /tmp/python-client
```

```
swagger-codegen generate -i /tmp/swagger.yaml -l python -o /tmp/python-client
```

## Relevant Links

* [swagger-codegen](https://github.com/swagger-api/swagger-codegen) - The full swagger codegen documentation
* [Swagger Documentation](https://github.com/fungible-inc/FunAPIGateway/blob/master/spec/v1/swagger.yaml) - Fungible Controller Swagger Documentation




