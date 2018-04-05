#include "stccppapi.h"
#include "stccapi.h"

#include <stdexcept>
#include <cassert>

using namespace stc;

namespace StccppapiImpl {

	static void ThrowCurrentError();
	static void CheckRet(int ret);

	class StcStr 
	{
	public:
		StcStr(const char* str, bool throwOnNull=true):_str(str) 
		{
			if (_str == NULL && throwOnNull)
				ThrowCurrentError();
		}

		~StcStr() 
		{ 
			if (_str)
			{
				stccapi_free_string(_str); 
				_str = NULL;
			}
		}

		std::string ToString() const 
		{
			if (_str == NULL)
				return "";

			return std::string(_str);			
		}

	private:
		const char * _str;
		StcStr();
		StcStr(const StcStr&);
		StcStr& operator = (const StcStr&);
	};

	class StcStrVec 
	{
	public:
		StcStrVec(stccapi_str_vector_t* vec):_vec(vec)
		{
			if (_vec == NULL)
				ThrowCurrentError();
		}

		StcStrVec():_vec(stccapi_str_vector_create())
		{
			if (_vec == NULL)
				ThrowCurrentError();
		}

		~StcStrVec()
		{
			assert(_vec);
			stccapi_str_vector_delete(_vec);
		}

		void CopyFrom(const StringMap& m)
		{
			for (StringMap::const_iterator it = m.begin(); it != m.end(); ++it)
			{
				CheckRet( stccapi_str_vector_append(_vec, it->first.c_str()) );
				CheckRet( stccapi_str_vector_append(_vec, it->second.c_str()) );
			}
		}

		void CopyFrom(const StringVector& v)
		{
			for (StringVector::const_iterator it = v.begin(); it != v.end(); ++it)
			{
				CheckRet( stccapi_str_vector_append(_vec, it->c_str()) );
			}
		}

		void CopyTo(StringMap& m) const
		{
			const int size = stccapi_str_vector_get_size(_vec);

			if (size == 1)
			{
				StcStr val(stccapi_str_vector_get_item(_vec, 0));
				m[""] = val.ToString();
				return;
			}

			assert((size % 2) == 0);
			for (int i = 0; i < size; )
			{
				StcStr key(stccapi_str_vector_get_item(_vec, i++));
				StcStr val(stccapi_str_vector_get_item(_vec, i++));
				m[key.ToString()] = val.ToString();
			}
		}

		void CopyTo(StringVector& v) const
		{
			const int size = stccapi_str_vector_get_size(_vec);
			for (int i = 0; i < size; ++i)
			{
				StcStr val(stccapi_str_vector_get_item(_vec, i));
				v.push_back(val.ToString());
			}
		}

		stccapi_str_vector_t* GetCApiPtr() const { return _vec; }

	private:
		stccapi_str_vector_t* _vec;
		StcStrVec(const StcStrVec&);
		StcStrVec& operator = (const StcStrVec&);
	};

	static void ThrowCurrentError()
	{
		StcStr str(stccapi_get_last_err_msg(), false);
		throw std::runtime_error(str.ToString());
	}

	static void CheckRet(int ret)
	{
		if (ret != 0)
			ThrowCurrentError();
	}
}

using namespace StccppapiImpl;

void stc::Log(const std::string& logLevel, const std::string& msg)
{
    CheckRet( stccapi_log(logLevel.c_str(), msg.c_str()) ); 
}

void stc::Init(void) 
{ 
    CheckRet( stccapi_init() ); 
}

void stc::Shutdown(void)
{
    CheckRet( stccapi_shutdown() ); 
}

void stc::Shutdown(int exitCode)
{
    CheckRet( stccapi_shutdown_with_exit_code(exitCode) ); 
}

void stc::Destroy(void)
{
    CheckRet( stccapi_shutdown_no_exit() );
}

std::string stc::Create(const std::string& type, const std::string& parent, 
        const StringMap& propertyPairs)
{
    StcStrVec vec;

	StringMap parentMap;
	parentMap["under"] = parent;
	vec.CopyFrom(parentMap);

    vec.CopyFrom(propertyPairs);

    StcStr str(stccapi_create(type.c_str(), vec.GetCApiPtr()));
    return str.ToString();
}

void stc::Delete(const std::string& handle)
{
    CheckRet( stccapi_delete(handle.c_str()) );
}

void stc::Config(const std::string& handle, 
				 const std::string& name, 
				 const std::string& value)
{
	StringMap propMap;
	propMap[name] = value;

	StcStrVec vec;
	vec.CopyFrom(propMap);
    CheckRet( stccapi_config(handle.c_str(), vec.GetCApiPtr()) );
}

void stc::Config(const std::string& handle, const StringMap& propertyPairs)
{
    StcStrVec vec;
    vec.CopyFrom(propertyPairs);
    CheckRet( stccapi_config(handle.c_str(), vec.GetCApiPtr()) );
}

StringMap stc::Get(const std::string& handle, const StringVector& propertyNames)
{
    StringMap ret;
    StcStrVec vec;
    vec.CopyFrom(propertyNames);
    StcStrVec retVec( stccapi_get(handle.c_str(), vec.GetCApiPtr()) );
    retVec.CopyTo(ret);

	StringMap::iterator it = ret.find("");
	if (it != ret.end() && !propertyNames.empty())
	{
		ret[propertyNames[0]] = it->second;
		ret.erase(it);
	}

    return ret;
}

std::string stc::Get(const std::string& handle, const std::string& propertyName)
{
    StringVector ret;
    StcStrVec vec;
	vec.CopyFrom( StringVector(1, propertyName) );
    StcStrVec retVec( stccapi_get(handle.c_str(), vec.GetCApiPtr()) );
    retVec.CopyTo(ret);

	if (ret.empty())
		return "";
	else
		return ret[0];
}

StringMap stc::Perform(const std::string& commandName, const StringMap& propertyPairs)
{
    StringMap ret;
    StcStrVec vec;
    vec.CopyFrom(propertyPairs);
    StcStrVec retVec( stccapi_perform(commandName.c_str(), vec.GetCApiPtr()) );
    retVec.CopyTo(ret);
    return ret;
}

void stc::Connect(const StringVector& hostNames)
{
    StcStrVec vec;
    vec.CopyFrom(hostNames);
    CheckRet( stccapi_connect(vec.GetCApiPtr()) );
}

void stc::Disconnect(const StringVector& hostNames)
{
    StcStrVec vec;
    vec.CopyFrom(hostNames);
    CheckRet( stccapi_disconnect(vec.GetCApiPtr()) );
}

StringVector stc::Reserve(const StringVector& CSPs)
{
    StringVector ret;
    StcStrVec vec;
    vec.CopyFrom(CSPs);
    StcStrVec retVec( stccapi_reserve(vec.GetCApiPtr()) );
    retVec.CopyTo(ret);
    return ret;
}

void stc::Release(const StringVector& CSPs)
{
    StcStrVec vec;
    vec.CopyFrom(CSPs);
    CheckRet( stccapi_release(vec.GetCApiPtr()) );
}

std::string stc::Subscribe(const StringMap& inputParameters)
{
    StcStrVec vec;
    vec.CopyFrom(inputParameters);
    StcStr str(stccapi_subscribe(vec.GetCApiPtr()));
    return str.ToString();
}

void stc::Unsubscribe(const std::string& handle)
{
    CheckRet( stccapi_unsubscribe(handle.c_str()) );
}

void stc::Apply(void)
{
    CheckRet( stccapi_apply() );
}

std::string  stc::WaitUntilComplete(const StringMap& inputParameters)
{
    StcStrVec vec;
    vec.CopyFrom(inputParameters);
    StcStr str(stccapi_wait_until_complete(vec.GetCApiPtr()));
    return str.ToString();
}

StringVector stc::TokenizeString(const std::string& str, const std::string& sep)
{
	StringVector vec;
    std::string::size_type curPos = 0;
    std::string::size_type prePos = 0;
    std::string::size_type length = 0;

    while (curPos != std::string::npos)
    {
        prePos = str.find_first_not_of(sep, curPos);
        if (prePos == std::string::npos)
            break;

        if (str[prePos] == '{')
        {
            curPos = str.find_first_of('}', prePos);
            if (curPos == std::string::npos)
				throw std::runtime_error((std::string)"Invalid \"" + str + "\": unmatched left brace");

            // skip actual braces
            ++prePos;
            length = (curPos - prePos);
            ++curPos;
        }
        else
        {
            curPos = str.find_first_of(sep, prePos);
            length = curPos - prePos;
        }

        std::string curVal = str.substr(prePos, length);
		vec.push_back(curVal);
    }

	return vec;
}

std::string stc::JoinStrings(const StringVector& strings, const std::string& sep)
{
    if (strings.empty())
        return "";

	std::string output;
    for (unsigned i = 0; i < strings.size(); ++i)
    {
        if (i != 0)
        {
            output += sep;
        }

        const std::string& str = strings[i];
        if (str.empty() || str.find_first_of(sep) != std::string::npos)
        {
            output += "{";
            output += str;
            output += "}";
        }
        else
        {
            output += str;
        }
    }

    return output;
}

