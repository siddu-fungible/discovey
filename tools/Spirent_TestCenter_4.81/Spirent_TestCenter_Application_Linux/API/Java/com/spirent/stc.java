package com.spirent;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import java.util.Vector;

public class stc
{        
	public static void Init() {

	    String installDir = System.getProperty("stc.dir");
	    if(installDir == null)
	    {
	        throw new RuntimeException("stc.dir property is not defined. It should be set to the STC install directory.");
	    }
	    	    
	    File iniFilePath = new File(installDir, "stcbll.ini");
	    if(iniFilePath.exists() == false)
	    {
	        throw new RuntimeException(installDir + " is not a valid STC install directory.");
	    }
	    
	    String stcLib = ( System.getProperty("os.name").toLowerCase().startsWith("win") ) ? "sJava.dll" : "libsJava.so";
	    System.load(installDir + File.separatorChar + stcLib);
	    
		try
		{		    
			stcJNI.setEnv("STC_PRIVATE_INSTALL_DIR=" + installDir);
		}
		catch (Exception e) { System.out.println("Setting environment failed: " + e); }
		sJava.salInit();
	}

	public static void Log(final String logLevel, final String msg) {
		sJava.salLog(logLevel, msg);
	}

	public static void Shutdown() {
		sJava.salShutdown();
	}

	public static void Connect(final String hostName) {
		StringVector sv = new StringVector();
		sv.add(hostName);
		sJava.salConnect(sv);
	}

	public static void Connect(final Vector<String> hostNames) {
		StringVector sv = new StringVector();
		for(int i = 0; i < hostNames.size(); i++)
			sv.add(hostNames.get(i));
		sJava.salConnect(sv);
	}

	public static void Disconnect(final String hostName) {
		StringVector sv = new StringVector();
		sv.add(hostName);
		sJava.salDisconnect(sv);
	}

	public static void Disconnect(final Vector<String> hostNames) {
		StringVector sv = new StringVector();
		for (int i = 0; i < hostNames.size(); i++)
			sv.add(hostNames.get(i));
		sJava.salDisconnect(sv);
	}

	public static String Create(final String type, final String parent) {
		StringVector sv = new StringVector();
		sv.add("-under");
		sv.add(parent);
		return sJava.salCreate(type, sv);
	}

	public static String Create(final String type, final String parent, final Map<String, String> propertyPairs) {
		StringVector sv = new StringVector();
		sv.add("-under");
		sv.add(parent);
		mapToStringVector(propertyPairs, sv);

		return sJava.salCreate(type, sv);
	}

	public static void Delete(final String handle) {
		sJava.salDelete(handle);
	}

	public static void Config(final String handle, final String attribName, final String attribValue) {
		StringVector sv = new StringVector();
		sv.add("-" + attribName);
		sv.add(attribValue);
		sJava.salSet(handle, sv);
	}

	public static void Config(final String handle, final Map<String, String> propertyPairs) {
		StringVector sv = new StringVector();
		mapToStringVector(propertyPairs, sv);
		sJava.salSet(handle, sv);
	}

	public static Map<String, String> Get(final String handle) {
		return stringVectorToMap(sJava.salGet(handle, new StringVector()));
	}

	public static Map<String, String> Get(final String handle, final Vector<String> properties) {

		StringVector sv = sJava.salGet(handle, vectorStringToStringVector(properties));		
		return unpackGetResponseAndReturnKeyVal(sv, properties);		
	}

	public static String Get(final String handle, final String property) {
		StringVector sv = new StringVector();
		sv.add("-" + property);
		StringVector sv2 = sJava.salGet(handle, sv);
		return sv2.get(0);
	}

	public static Map<String, String> Perform(final String commandName) {
		return stringVectorToMap(sJava.salPerform(commandName, new StringVector()));
	}

	public static Map<String, String> Perform(final String commandName, final Map<String, String> propertyPairs) {

		StringVector sv = new StringVector();
		mapToStringVector(propertyPairs, sv);
		StringVector retSv = sJava.salPerform(commandName, sv);
		return unpackPerformResponseAndReturnKeyVal(retSv, propertyPairs);
	}

	public static void Reserve(final String CSP) {
		StringVector sv = new StringVector();
		sv.add(CSP);
		sJava.salReserve(sv);
	}

	public static void Reserve(final Vector<String> CSPs) {
		StringVector sv = new StringVector();
		for(int i = 0; i < CSPs.size(); i++)
			sv.add(CSPs.get(i));
		sJava.salReserve(sv);
	}

	public static void Release(final String CSP) {
		StringVector sv = new StringVector();
		sv.add(CSP);
		sJava.salRelease(sv);
	}

	public static void Release(final Vector<String> CSPs) {
		StringVector sv = new StringVector();
		for(int i = 0; i < CSPs.size(); i++)
			sv.add(CSPs.get(i));
		sJava.salRelease(sv);
	}

	public static String Subscribe(final Map<String, String> inputParameters) {
		StringVector sv = new StringVector();
		mapToStringVector(inputParameters, sv);
		return sJava.salSubscribe(sv);
	}

	public static void Unsubscribe(final String handle) {
		sJava.salUnsubscribe(handle);
	}

	public static void Apply() {
		sJava.salApply();
	}
	
	public static String WaitUntilComplete()
    {
        return DoWaitUntilComplete(0);
    }

    public static String WaitUntilComplete(int timeoutInSec)
    {
        return DoWaitUntilComplete(timeoutInSec);
    }

    private static String DoWaitUntilComplete(int timeoutInSec) {
        String seq = stc.Get("system1", "children-sequencer");
        int timer = 0;
        while(true) {
            String curTestState = stc.Get(seq, "state");
            if(curTestState.equals("PAUSE") || curTestState.equals("IDLE")) {
                break;
            }
            
            try {
                Thread.sleep(1000);
            }
            catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            timer += 1;
            if(timeoutInSec > 0 && timer > timeoutInSec) {                    
                throw new RuntimeException(String.format("ERROR: Stc.WaitUntilComplete timed out after %1$s sec", timeoutInSec));
            }                
        }
        
        String syncFiles = System.getenv("STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE");
        if(syncFiles != null && syncFiles.equals("1") &&
            stc.Perform("CSGetBllInfo").get("ConnectionType").equals("SESSION")) {
            stc.Perform("CSSynchronizeFiles");
        }

        return stc.Get(seq, "testState");
    }                       

	public static String JoinString(final Vector<String> vs) {
		String s = new String();
		for(int i = 0; i < vs.size(); i++) {
			s += vs.get(i) + " ";
		}
		return s.substring(0,s.length() - 1);
	}

	static void mapToStringVector(Map<String, String> sm, StringVector sv) {
	    for(Map.Entry<String, String> entry : sm.entrySet()) {
	        sv.add("-" + entry.getKey());
            sv.add(entry.getValue());
	    }		 	
	}

	static Map<String,String> stringVectorToMap(StringVector sv) {

		Map<String, String> sm = new HashMap<String, String>();
		for(int i = 0; i < sv.size(); i += 2) {
			sm.put(sv.get(i).substring(1, sv.get(i).length()), sv.get(i + 1));		//take out the dash
		}
		return sm;
	}
	
	static StringVector vectorStringToStringVector(Vector<String> vs) {

		StringVector sv = new StringVector();
		for (int i = 0; i < vs.size(); i++) {
			sv.add("-" + vs.get(i));
		}
		return sv;
	}
	
	static Map<String, String> unpackGetResponseAndReturnKeyVal(StringVector sv, Vector<String> props) {
        Map<String, String> propVals = new HashMap<String, String>();            
        for(int i = 0; i < (sv.size()/2); ++i) {
            String key = props.get(i);
            String val = sv.get(i*2 + 1);
            propVals.put(key, val);
        }

        return propVals;
    }
	
	static Map<String, String> unpackPerformResponseAndReturnKeyVal(StringVector sv, Map<String, String> origKeys) {   
        Map<String, String> origKeyHash = new HashMap<String, String>();
        for(String key : origKeys.keySet()) {
            origKeyHash.put(key.toLowerCase(), key);
        }        
        
        Map<String, String> retVals = new HashMap<String, String>();
        for(int i = 0; i < (sv.size() / 2); ++i) {
            String key = sv.get(i*2).substring(1, sv.get(i*2).length());
            String val = sv.get(i*2 + 1);
            if(origKeyHash.containsKey(key.toLowerCase())) {
                key = origKeyHash.get(key.toLowerCase());
            }

            retVals.put(key, val);
        }

        return retVals;
    }
}
