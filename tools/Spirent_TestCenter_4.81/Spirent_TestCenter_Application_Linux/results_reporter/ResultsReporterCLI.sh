#!/bin/sh

rrPath=`dirname "$0"`
cd $rrPath

rrDateTime=`date +%m-%d-%Y-%H-%M-%S-%N`
rrLogDir=~/.spirent/ResultsReporterLog/${rrDateTime}
rrLogFile="${rrLogDir}/${rrDateTime}.log"

mkdir -p ${rrLogDir}
OUT=$?
if [ $OUT -ne 0 ];
then
   echo "Could not create log file directory at ${rrLogDir}. Redirecting output to /dev/null"
   rrLogFile=/dev/null
fi

if (test "$LD_LIBRARY_PATH" = "") then
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:bin:..
else
  LD_LIBRARY_PATH=bin:..
fi
export LD_LIBRARY_PATH

CLASSPATH=./lib/Analyzer.jar:./lib/com.spirent.tc.core.proxy_1.0.0.jar:./lib/commons-cli-1.0.jar:./lib/core-renderer.jar:./lib/core-renderer-minimal.jar:./lib/derby.jar:./lib/derbyclient.jar:./lib/derbynet.jar:./lib/dom4j-full.jar:./lib/h2.jar:./lib/iText.jar:./lib/jacl.jar:./lib/jcommon-1.0.13.jar:./lib/jdom.jar:./lib/jfreechart-1.0.13.jar:./lib/jna.jar:./lib/junit-4.7.jar:./lib/log4j-1.2.15.jar:./lib/lucene-core-2.4.1.jar:./lib/OfficeLnFs_2.7.jar:./lib/org.eclipse.core.commands_3.3.0.I20070605-0010.jar:./lib/org.eclipse.core.databinding.observable_1.2.0.M20090902-0800.jar:./lib/org.eclipse.core.runtime_3.3.100.v20070530.jar:./lib/org.eclipse.equinox.common_3.3.0.v20070426.jar:./lib/org.eclipse.equinox.registry_3.3.1.R33x_v20070802.jar:./lib/org.eclipse.jface_3.3.2.M20080207-0800.jar:./lib/org.eclipse.osgi_3.3.2.R33x_v20080105.jar:./lib/org.eclipse.swt.win32.win32.x86_3.5.0.v3550b.jar:./lib/org.eclipse.swt_3.5.0.v3550b.jar:./lib/org.eclipse.ui_3.3.1.M20071128-0800.jar:./lib/org.eclipse.ui.workbench_3.3.2.M20080207-0800.jar:./lib/poi-3.10.1-20140818.jar:./lib/poi-ooxml-3.10.1-20140818.jar:./lib/poi-ooxml-schemas-3.10.1-20140818.jar:./lib/xmlbeans-2.6.0.jar:./lib/sqlite.jar:./lib/swank.jar:./lib/sJava.jar:./lib/swingx-1.0.jar:./lib/tc.jar:./lib/tcljava.jar:./lib/wizard.jar:./lib/Zql.jar:./lib/jcchart.jar:./lib/javamail-1.4.1.jar:./lib/pdfbox-1.3.1.jar:

export CLASSPATH


_jvm/bin/java -mx768m -Djdbc.drivers=org.apache.derby.jdbc.EmbeddedDriver -Djdbc.drivers=SQLite.JDBCDriver -Djava.awt.headless=true -Djava.library.path=bin:.. -cp ${CLASSPATH} com.caw.analyzer.CLI "$@" > ${rrLogFile} 2>&1
