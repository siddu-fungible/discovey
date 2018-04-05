// Copyright (c) 2010 by Spirent Communications, Inc.
// All Rights Reserved
//
// By accessing or executing this software, you agree to be bound 
// by the terms of this agreement.
// 
// Redistribution and use of this software in source and binary forms,
// with or without modification, are permitted provided that the 
// following conditions are met:
//   1.  Redistribution of source code must contain the above copyright 
//       notice, this list of conditions, and the following disclaimer.
//   2.  Redistribution in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer
//       in the documentation and/or other materials provided with the
//       distribution.
//   3.  Neither the name Spirent Communications nor the names of its
//       contributors may be used to endorse or promote products derived
//       from this software without specific prior written permission.
//
// This software is provided by the copyright holders and contributors 
// [as is] and any express or implied warranties, including, but not 
// limited to, the implied warranties of merchantability and fitness for
// a particular purpose are disclaimed.  In no event shall Spirent
// Communications, Inc. or its contributors be liable for any direct, 
// indirect, incidental, special, exemplary, or consequential damages
// (including, but not limited to: procurement of substitute goods or
// services; loss of use, data, or profits; or business interruption)
// however caused and on any theory of liability, whether in contract, 
// strict liability, or tort (including negligence or otherwise) arising
// in any way out of the use of this software, even if advised of the
// possibility of such damage.

// File Name:                 Anatomy.cpp
// Description:               This script demonstrates basic features 
//                            such as creating streams, generating traffic,
//                            enabling capture, saving realtime results
//                            to files, and retrieving results.

#include "stccppapi.h"
#include <stdexcept>
#include <iostream>

#ifdef WIN32
#include <windows.h>
#else
#include <unistd.h>
#define Sleep(x) usleep((x)*1000)
#endif 

int main()
{
	bool ENABLE_CAPTURE = true;
	stc::StringMap props;

	std::string stcVersion = stc::Get("system1", "Version");
	std::cout << "SpirentTestCenter system version:\t" << stcVersion << std::endl;
	
	// Physical topology
	std::string szChassisIp1 = "10.29.0.49";
	std::string szChassisIp2 = "10.29.0.45";
	std::string txPortLoc = "//" + szChassisIp1 + "/1/1";
	std::string rxPortLoc = "//" + szChassisIp2 + "/1/1";

	// Create the root project object
	std::cout << "Creating project ...\n";
	std::string hProject = stc::Create("project", "system1");

	// Create ports
	std::cout << "Creating ports ...\n";
	props.clear();
	props["location"] = txPortLoc;
	props["useDefaultHost"] = "false";
	std::string hPortTx = stc::Create("port", hProject, props);
	props.clear();
	props["location"] = rxPortLoc;
	props["useDefaultHost"] = "false";
	std::string hPortRx = stc::Create("port", hProject, props);

	// Configure ethernet Fiber interface.
	stc::Create("EthernetCopper", hPortTx);

	// Attach ports. 
    // Connects to chassis, reserves ports and sets up port mappings all in one step.
    // By default, connects to all previously created ports.
	std::cout << "Attaching ports " << txPortLoc << " " <<  rxPortLoc << std::endl;
	stc::Perform("AttachPorts");

	// Apply the configuration.
	std::cout << "Apply configuration\n";
	stc::Apply();

	// Initialize generator/analyzer.
	std::string hGenerator = stc::Get(hPortTx, "children-Generator");
	std::string stateGenerator = stc::Get(hGenerator, "state");
	std::cout << "Stopping Generator -current state " + stateGenerator << std::endl;
	props.clear();
	props["GeneratorList"] = hGenerator;
	stc::Perform("GeneratorStop", props); 

	std::string hAnalyzer = stc::Get(hPortRx, "children-Analyzer");
	std::string stateAnalyzer = stc::Get(hAnalyzer, "state");
	std::cout << "Stopping Analyzer -current state " + stateAnalyzer << std::endl;
	props.clear();
	props["AnalyzerList"] = hAnalyzer;
	stc::Perform("AnalyzerStop", props); 

	// Create a stream block. FrameConfig with blank double quotes clears the frame out.
	std::cout << "Configuring stream block ...\n";
	props.clear();
	props["insertSig"] = "true";
	props["frameConfig"] = "";
	props["frameLengthMode"] = "FIXED";
	props["maxFrameLength"] = "1200";
	props["FixedFrameLength"] = "256";
	std::string hStreamBlock = stc::Create("streamBlock", hPortTx, props);

	// Add an EthernetII Protocol Data Unit (PDU).
	std::cout << "Adding headers\n";
	props.clear();
	props["name"] = "sb1_eth";
	props["srcMac"] = "00:00:20:00:00:00";
	props["dstMac"] = "00:00:00:00:00:00";
	stc::Create("ethernet:EthernetII", hStreamBlock, props);

	// Use modifier to generate multiple streams.
	std::cout << "Creating Modifier on Stream Block ...\n";
	props.clear();
	props["ModifierMode"] = "INCR";  
	props["Mask"] = "0000FFFFFFFF";
	props["StepValue"] = "000000000001";
	props["Data"] = "000000000000";
	props["RecycleCount"] = "4294967295";
	props["RepeatCount"] = "0";
	props["DataType"] = "BYTE";
	props["EnableStream"] = "FALSE";
	props["Offset"] = "0";
	props["OffsetReference"] = "sb1_eth.dstMac";
	std::string hRangeModifier = stc::Create("RangeModifier", hStreamBlock, props);

	// Configure generator
	std::cout << "Configuring Generator\n";
	std::string hGeneratorConfig = stc::Get(hGenerator, "children-GeneratorConfig");
	props.clear();
	props["DurationMode"] = "SECONDS"; 
	props["BurstSize"] = "1"; 
	props["Duration"] = "100"; 
	props["LoadMode"] = "FIXED"; 
	props["FixedLoad"] = "25"; 
	props["LoadUnit"] = "PERCENT_LINE_RATE"; 
	props["SchedulingMode"] = "PORT_BASED"; 
	stc::Config(hGeneratorConfig, props);

	// Analyzer Configuration
	std::cout << "Configuring Analyzer\n";
	std::string hAnalyzerConfig = stc::Get(hAnalyzer, "children-AnalyzerConfig");

	// Subscribe to realtime results
	std::cout << "Subscribe to results\n";
	props.clear();
	props["Parent"] = hProject; 
	props["ConfigType"] = "Analyzer"; 
	props["resulttype"] = "AnalyzerPortResults"; 
	props["filenameprefix"] = "Analyzer_Port_Results"; 
	stc::Subscribe(props);

	props.clear();
	props["Parent"] = hProject; 
	props["ConfigType"] = "Generator"; 
	props["resulttype"] = "GeneratorPortResults"; 
	props["filenameprefix"] = "Generator_Port_Counter"; 
	stc::Subscribe(props);

	// Configure Capture.
	std::string hCapture;
	if (ENABLE_CAPTURE)
	{
		std::cout << "\nStarting Capture...\n";
  
		// Create a capture object. Automatically created.
		hCapture = stc::Get(hPortRx, "children-capture");
		props.clear();
		props["mode"] = "REGULAR_MODE"; 
		props["srcMode"] = "TX_RX_MODE"; 
		stc::Config(hCapture, props);
		props.clear();
		props["captureProxyId"] = hCapture; 
		stc::Perform("CaptureStart", props);
	}

	// Apply configuration.  
	std::cout << "Apply configuration\n";
	stc::Apply();

	// Save the configuration as an XML file for later import into the GUI.
	std::cout << "\nSave configuration as an XML file.\n";
	stc::Perform("SaveAsXml");

	// Start the analyzer and generator.
	std::cout << "Start Analyzer\n";
	props.clear();
	props["AnalyzerList"] = hAnalyzer; 
	stc::Perform("AnalyzerStart", props);
	stateAnalyzer = stc::Get(hAnalyzer, "state");
	std::cout << "Current analyzer state " + stateAnalyzer << std::endl;

	Sleep(2000);
	
	std::cout << "Start Generator\n";
	props.clear();
	props["GeneratorList"] = hGenerator; 
	stc::Perform("GeneratorStart", props);
	stateGenerator = stc::Get(hGenerator, "state");
	std::cout << "Current generator state " << stateGenerator << std::endl;

	std::cout << "Wait 5 seconds ...\n";
	Sleep(5000);

	stateAnalyzer = stc::Get(hAnalyzer, "state");
	stateGenerator = stc::Get(hGenerator, "state");
	std::cout << "Current analyzer state " << stateAnalyzer << std::endl;
	std::cout << "Current generator state " << stateGenerator << std::endl;
	std::cout << "Stop Analyzer\n";
	
	// Stop the analyzer.  
	props.clear();
	props["AnalyzerList"] = hAnalyzer; 
	stc::Perform("AnalyzerStop", props);
	Sleep(1000);
	
	// Display some statistics.

	std::cout << "Frames Counts:" << std::endl;
    // Example of Direct-Descendant Notation ( DDN ) syntax. ( DDN starts with an object reference )  
	std::string sigFrameCount = stc::Get(hAnalyzer + ".AnalyzerPortResults(1)", "sigFrameCount");
    std::string totalFrameCount = stc::Get(hAnalyzer + ".AnalyzerPortResults(1)", "totalFrameCount");
	std::cout << "\tSignature frames: " << sigFrameCount << std::endl;
	std::cout << "\tTotal frames: " << totalFrameCount << std::endl;

	// Example of Descendant-Attribute Notation ( DAN ) syntax. ( using explicit indeces )
	std::string minFrameLength = stc::Get(hPortRx, "Analyzer(1).AnalyzerPortResults(1).minFrameLength");
	std::cout << "\tMinFrameLength: " << minFrameLength << std::endl;
	// Notice indexing is not necessary since there is only 1 child. 
	std::string maxFrameLength = stc::Get(hPortRx, "Analyzer.AnalyzerPortResults.maxFrameLength");
	std::cout << "\tMaxFrameLength: " << maxFrameLength << std::endl;

	if (ENABLE_CAPTURE)
	{
		std::cout << "Retrieving Captured frames...\n";
		props.clear();
		props["captureProxyId"] = hCapture; 
		stc::Perform("CaptureStop", props);
    
		// Save captured frames to a file.
		props.clear();
		props["captureProxyId"] = hCapture; 
		props["FileName"] = "capture.pcap"; 
		props["FileNameFormat"] = "PCAP"; 
		props["IsScap"] = "FALSE"; 
		stc::Perform("CaptureDataSave", props);
   
		std::string pktCount = stc::Get(hCapture, "PktCount");
		std::cout << "Captured frames:\t" + pktCount << std::endl;
	}

	// Disconnect from chassis, release ports, and reset configuration.
	std::cout << "Release ports and disconnect from chassis." << std::endl;
	stc::Perform("ChassisDisconnectAll");	
	stc::Perform("ResetConfig");
		
	// Delete configuration
	std::cout << "Deleting project\n";
	stc::Delete(hProject);

	return 0;
}

