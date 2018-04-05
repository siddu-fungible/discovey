#ifndef STCCPPAPI_H
#define STCCPPAPI_H

#define STC_EXPORT 

#ifdef WIN32
#pragma warning (disable:4786)
#endif

#include <map>
#include <vector>
#include <string>

namespace stc {

	typedef std::map<std::string, std::string> StringMap;
    typedef std::vector<std::string>           StringVector;


    STC_EXPORT std::string  Create(const std::string& type, const std::string& parent, 
                                   const StringMap& propertyPairs = StringMap());
    STC_EXPORT void         Delete(const std::string& handle);

	STC_EXPORT void         Config(const std::string& handle, 
                                   const std::string& name, const std::string& value);
    STC_EXPORT void         Config(const std::string& handle, const StringMap& propertyPairs);

    STC_EXPORT StringMap    Get(const std::string& handle, 
                                const StringVector& propertyNames = StringVector());
	STC_EXPORT std::string  Get(const std::string& handle, const std::string& propertyName);

    STC_EXPORT StringMap    Perform(const std::string& commandName, 
                                    const StringMap& propertyPairs = StringMap());

	STC_EXPORT StringVector TokenizeString(const std::string& str, const std::string& sep = " ");
	STC_EXPORT std::string  JoinStrings(const StringVector& strs, const std::string& sep = " ");

    STC_EXPORT void         Log(const std::string& logLevel, const std::string& msg);
    STC_EXPORT void         Apply(void);
    STC_EXPORT std::string  Subscribe(const StringMap& inputParameters);
    STC_EXPORT void         Unsubscribe(const std::string& handle);
	STC_EXPORT std::string  WaitUntilComplete(const StringMap& inputParameters = StringMap());

    STC_EXPORT void         Connect(const StringVector& hostNames);
    STC_EXPORT void         Disconnect(const StringVector& hostNames);
    STC_EXPORT StringVector Reserve(const StringVector& CSPs);
    STC_EXPORT void         Release(const StringVector& CSPs);

    STC_EXPORT void Init(void);
    STC_EXPORT void Shutdown(void);
    STC_EXPORT void Shutdown(int exitCode);
    STC_EXPORT void Destroy(void);
}

#endif

