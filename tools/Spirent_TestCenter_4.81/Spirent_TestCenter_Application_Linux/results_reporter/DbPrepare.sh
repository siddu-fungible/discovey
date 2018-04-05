#!/bin/sh

if (test "$LD_LIBRARY_PATH" = "") then
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:bin
else
  LD_LIBRARY_PATH=bin
fi
export LD_LIBRARY_PATH

CLASSPATH=./lib/Analyzer.jar:./lib/dom4j-full.jar:./lib/iText.jar:./lib/jfreechart-1.0.10.jar:./lib/jcommon-1.0.13.jar:./lib/tcljava.jar:./lib/jacl.jar:./lib/commons-cli-1.0.jar:./lib/Zql.jar:./lib/sqlite.jar:./lib/OfficeLnFs_2.7.jar:./lib/jcchart.jar
export CLASSPATH


_jvm/bin/java -mx256m -Djava.library.path=bin -cp ${CLASSPATH} com.caw.analyzer.DbPrepare $*
