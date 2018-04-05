#include "stccppapi.h"

#include <stdexcept>
#include <iostream>

#ifdef WIN32
#include <windows.h>
#else
#include <unistd.h>
#define Sleep(x) usleep((x)*1000)
#endif 

void SampleTest()
{
	const std::string resultTemplateUri = "Result Views/Port Traffic/Basic Traffic Results.xml";
	const std::string project = stc::Get("system1", "children-Project");
	const std::string chassis = "10.100.20.78";
	const int streamCount = 1;
	const int trafficDurationInMS = 3000;

	stc::StringMap props;
	stc::StringVector ports;
	stc::StringVector portLocs;
	unsigned i = 0;
	unsigned j = 0;

	portLocs.push_back("//" + chassis + "/2/9");
	portLocs.push_back("//" + chassis + "/2/10");


	std::cout << "Creating ports/streams" << std::endl;
	for (i = 0; i < portLocs.size(); ++i)
	{
		props.clear();
		props["location"] = portLocs[i];
		const std::string port = stc::Create("port", project, props);
		ports.push_back(port);

		for (j = 0; j < streamCount; ++j)
		{
			stc::Create("streamBlock", port);
		}
	}


	std::cout << "Loading template: " << resultTemplateUri << std::endl;
	props.clear();
	props["parentConfig"] = project;
	props["templateUri"] = resultTemplateUri;
	const std::string resultDataSet = stc::Perform("createFromTemplate", props)["Config"];

	std::cout << "Subscribing " << resultTemplateUri << std::endl;
	props.clear();
	props["resultRootList"] = project;
	stc::StringVector qrys = stc::TokenizeString(
		stc::Get(resultDataSet, "children-ResultQuery"));
	for (i = 0; i < qrys.size(); ++i)
	{
		stc::Config(qrys[i], props);
	}
	props.clear();
	props["resultDataSet"] = resultDataSet;
	stc::Perform("resultDataSetSubscribe", props);


	std::cout << "Attaching ports" << std::endl;
	props.clear();
	props["portList"] = stc::JoinStrings(ports);
	props["autoConnect"] = "true";
	stc::Perform("attachPorts", props);

	std::cout << "Apply to IL" << std::endl;
	stc::Perform("applyToIL");


	std::cout << "Start analyzers" << std::endl;
	props.clear();
	props["analyzerList"] = project;
	stc::Perform("analyzerStart", props);


	std::cout << "Start generators" << std::endl;
	props.clear();
	props["generatorList"] = project;
	stc::Perform("generatorStart", props);


	std::cout << "Running traffic for " << trafficDurationInMS << " MS" << std::endl;
	Sleep(trafficDurationInMS);


	std::cout << "Stop generators" << std::endl;
	props.clear();
	props["generatorList"] = project;
	stc::Perform("generatorStop", props);

	std::cout << "Stop analyzers" << std::endl;
	props.clear();
	props["analyzerList"] = project;
	stc::Perform("analyzerStop", props);

	Sleep(1000);

	std::cout << "Port1 Total TX: " <<
		stc::Get("project1.port.1.generator.generatorPortResults", "TotalFrameCount")
		<< " Total RX: " << 
		stc::Get("project1.port.1.analyzer.analyzerPortResults", "TotalFrameCount")
		<< std::endl;

	std::cout << "Port2 Total TX: " <<
		stc::Get("project1.port.2.generator.generatorPortResults", "TotalFrameCount")
		<< " Total RX: " << 
		stc::Get("project1.port.2.analyzer.analyzerPortResults", "TotalFrameCount")
		<< std::endl;

	std::cout << "Disconnect" << std::endl;
	stc::Disconnect(stc::StringVector(1, chassis));
}


int main()
{
	try 
	{
		SampleTest();
		return 0;
	}
	catch (std::runtime_error& e)
	{
		std::cerr << e.what();
		return -1;
	}
}

