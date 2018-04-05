
module Stc 
    
    if RUBY_PLATFORM.downcase.index('win') != nil or RUBY_PLATFORM.downcase.index('mingw32') != nil
        begin
            ENV['STC_PRIVATE_INSTALL_DIR'] = STC_INSTALL_DIR 
        rescue 
            raise "Please replace STC_INSTALL_DIR with the actual STC install directory first, or set the system environment variable."
        end
    else
        if not ENV::has_key?('STC_PRIVATE_INSTALL_DIR')
            begin
                ENV['STC_PRIVATE_INSTALL_DIR'] = STC_INSTALL_DIR 
            rescue 
                raise "Please replace STC_INSTALL_DIR with the actual STC install directory first, or set the system environment variable."
            end
        end
    end

    if not File.directory? ENV['STC_PRIVATE_INSTALL_DIR'] or 
       not File.file? File.join(ENV['STC_PRIVATE_INSTALL_DIR'], 'stcbll.ini')
        raise "#{ENV['STC_PRIVATE_INSTALL_DIR']} is not a valid STC install directory."
    end

    runningDir = Dir.pwd()
    ENV['STC_SCRIPT_RUNNING_DIR'] = runningDir
    Dir.chdir(ENV['STC_PRIVATE_INSTALL_DIR'])
    if RUBY_PLATFORM.downcase.index('win') != nil or RUBY_PLATFORM.downcase.index('mingw32') != nil    
        require File.join(ENV['STC_PRIVATE_INSTALL_DIR'], 'StcIntRuby.dll')
    else        
        require File.join(ENV['STC_PRIVATE_INSTALL_DIR'], 'StcIntRuby.so')
    end
    Dir.chdir(runningDir)
    
    
    

    class << self

    def log(lvl, msg) 
        StcIntRuby.salLog(lvl, msg)
    end

    def create(type, parent, args={})
        svec = StcIntRuby::StringVector.new()
        svec.push('-under')
        svec.push(parent)
        svec.packKeyVal(args)
        return StcIntRuby.salCreate(type, svec)
    end

    def delete(handle)
        return StcIntRuby.salDelete(handle)
    end

    def config(handle, args)
        svec = StcIntRuby::StringVector.new()
        svec.packKeyVal(args)
        return StcIntRuby.salSet(handle, svec)
    end

    def get(handle, *args)

        svec = StcIntRuby::StringVector.new()
        args.flatten().each { |k| svec.push('-' + k) }
        retSvec = StcIntRuby::salGet(handle, svec)

        if retSvec.length == 1
            return retSvec[0]
        else
            return StcIntRuby::StringVector.unpackGetResponseAndReturnKeyVal(retSvec, args.flatten())
        end
    end

    def perform(oper, args={})
        svec = StcIntRuby::StringVector.new()
        svec.packKeyVal(args)
        retSvec = StcIntRuby.salPerform(oper, svec)
        return StcIntRuby::StringVector.unpackPerformResponseAndReturnKeyVal(retSvec, args.keys())
    end

    def apply()
        return StcIntRuby.salApply()
    end

    def help(topic="")
        if topic == '' or  topic.include?(' ') then
            return  "Usage: \n" +
                    "  Stc.help('commands')\n" +
                    "  Stc.help(<handle>)\n" +
                    "  Stc.help(<className>)\n" +
                    "  Stc.help(<subClassName>)"
        end

        if topic == 'commands' then
            return StcIntRuby::Help::HELP_INFO.values().map { 
                       |x| '  ' + x[:desc] 
                   }.sort().join("\n")
        end

        topic = 'waitUntilComplete' if topic == 'waituntilcomplete'
        info = StcIntRuby::Help::HELP_INFO[topic]
        if info != nil then
            return "Desc: " + info[:desc] + "\n" + 
                   "Usage: " + info[:usage] + "\n" + 
                   "Example: " + info[:example] + "\n"
        end

        return StcIntRuby.salHelp(topic)
    end

    def connect(host, *hosts)
        hosts.insert(0, host)
        svec = StcIntRuby::StringVector.new()
        hosts.flatten().each { |v| svec.push(v) }
        return StcIntRuby.salConnect(svec)
    end

    def disconnect(host, *hosts)
        hosts.insert(0, host)
        svec = StcIntRuby::StringVector.new()
        hosts.flatten().each { |v| svec.push(v) }
        return StcIntRuby.salDisconnect(svec)
    end

    def reserve(csp, *csps)
        csps.insert(0, csp)
        svec = StcIntRuby::StringVector.new()
        csps.flatten().each { |v| svec.push(v) }
        return StcIntRuby.salReserve(svec)
    end

    def release(csp, *csps)
        csps.insert(0, csp)
        svec = StcIntRuby::StringVector.new()
        csps.flatten().each { |v| svec.push(v) }
        return StcIntRuby.salRelease(svec)
    end

    def subscribe(args)
        svec = StcIntRuby::StringVector.new()
        svec.packKeyVal(args)
        return StcIntRuby.salSubscribe(svec)
    end

    def unsubscribe(arg)
        return StcIntRuby.salUnsubscribe(arg)
    end

    def destroy()
        Stc.perform('ChassisDisconnectAll')
        Stc.perform('ResetConfig', 'config'=>'system1')
        return StcIntRuby.salShutdownNoExit();
    end

    def waitUntilComplete(args={})

        timeout = Integer(args['timeout'])
        sequencer = Stc.get('system1', 'children-sequencer')
        timer = 0

        while true
            curTestState = Stc.get(sequencer, 'state')
            break if ["PAUSE", "IDLE"].include? curTestState

            sleep 1
            timer += 1

            if timeout > 0 and timer > timeout
                raise "ERROR: Stc.waitUntilComplete timed out after #{timeout} sec"
            end
        end  

        if ENV['STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE'] == "1" and
           Stc.perform('CSGetBllInfo')['ConnectionType'] == 'SESSION' then
            Stc.perform('CSSynchronizeFiles')
        end 

        return Stc.get(sequencer, 'testState')
    end

    
    # end of class << self
    end


    # Internal string vector helper functions
    class StcIntRuby::StringVector

        def packKeyVal(hash)
            for key,val in hash
                push('-' + key.to_s())
                if val.class == Array
                    push(val.join(' '))
                else
                    push(val.to_s())
                end
            end
        end

        def self.unpackGetResponseAndReturnKeyVal(svec, origKeys=[])
            useOrigKey = origKeys.size == svec.length/2
            hash = {}
            for i in 0..(svec.length/2 - 1)
                key = svec[i*2][1..-1]
                val = svec[i*2+1]
                if useOrigKey then key = origKeys[i] end
                hash[key] = val
            end
            return hash
        end

        def self.unpackPerformResponseAndReturnKeyVal(svec, origKeys=[])
            origKeyHash = {}
            origKeys.each { |k|  origKeyHash[k.downcase()] = k }

            hash = {}
            for i in 0..(svec.length/2 - 1)
                key = svec[i*2][1..-1]
                val = svec[i*2+1]
                key = origKeyHash.fetch(key.downcase(), key)
                hash[key] = val
            end
            return hash
        end

    end

    # internal help info
    class StcIntRuby::Help
        HELP_INFO = {
            "create"=>{
                        :desc       =>"create: -Creates an object in a test hierarchy",
                        :usage      =>"Stc.create( className, parentObjectHandle, propertyName1 => propertyValue1, ... )",
                        :example    =>'Stc.create( \'port\', project1, \'location\'=> "#{mychassis1}/1/2" )',
            },
            "config"=>{
                        :desc       =>"config: -Sets or modifies the value of an attribute",
                        :usage      =>"Stc.config( objectHandle, propertyName1 => propertyValue1, ... )",
                        :example    =>"Stc.config( stream1, 'enabled'=>true )",
            },
            "get"=>{
                        :desc       =>"get: -Retrieves the value of an attribute",
                        :usage      =>"Stc.get( objectHandle, propertyName1, propertyName2, ... )",
                        :example    =>"Stc.get( stream1, 'enabled', 'name' )",
            },
            "perform"=>{
                        :desc       =>"perform: -Invokes an operation",
                        :usage      =>"Stc.perform( commandName, propertyName1 => propertyValue1, ... )",
                        :example    =>"Stc.perform( 'createdevice', 'parentHandleList'=>project1 'createCount'=>4 )",
            },
            "delete"=>{
                        :desc       =>"delete: -Deletes an object in a test hierarchy",
                        :usage      =>"Stc.delete( objectHandle )",
                        :example    =>"Stc.delete( stream1 )",
            },
            "connect"=>{
                        :desc       =>"connect: -Establishes a connection with a Spirent TestCenter chassis",
                        :usage      =>"Stc.connect( hostnameOrIPaddress, ... )",
                        :example    =>"Stc.connect( mychassis1 )",
            },
            "disconnect"=>{
                        :desc       =>"disconnect: -Removes a connection with a Spirent TestCenter chassis",
                        :usage      =>"Stc.disconnect( hostnameOrIPaddress, ... )" ,
                        :example    =>"Stc.disconnect( mychassis1 )" ,
            },
            "reserve"=>{
                        :desc       =>"reserve: -Reserves a port group",
                        :usage      =>"Stc.reserve( CSP1, CSP2, ... )",
                        :example    =>'Stc.reserve( "//#{mychassis1}/1/1", "//#{mychassis1}/1/2" )'
            },
            "release"=>{
                        :desc       =>"release: -Releases a port group",
                        :usage      =>"Stc.release( CSP1, CSP2, ... )",
                        :example    =>'Stc.release( "//#{mychassis1}/1/1", "//#{mychassis1}/1/2" )'
            },
            "apply"=>{
                        :desc       =>"apply: -Applies a test configuration to the Spirent TestCenter firmware",
                        :usage      =>"Stc.apply()",
                        :example    =>"Stc.apply()",
            },
            "log"=>{
                        :desc       =>"log: -Writes a diagnostic message to the log file",
                        :usage      =>"Stc.log( logLevel, message )",
                        :example    =>"Stc.log( 'DEBUG', 'This is a debug message' )",
            },
            "waitUntilComplete"=>{
                        :desc       =>"waitUntilComplete: -Suspends your application until the test has finished",
                        :usage      =>"Stc.waitUntilComplete()",
                        :example    =>"Stc.waitUntilComplete()",
            },
            "subscribe"=>{
                        :desc       =>"subscribe: -Directs result output to a file or to standard output",
                        :usage      =>"Stc.subscribe( 'parent'=>parentHandle, 'resultParent'=>parentHandles, 'configType'=>configType, 'resultType'=>resultType, 'viewAttributeList'=>attributeList, 'interval'=>interval, 'fileNamePrefix'=>fileNamePrefix )",
                        :example    =>"Stc.subscribe( 'parent'=>project, 'configType'=>'Analyzer', 'resulttype'=>'AnalyzerPortResults', 'filenameprefix'=>'analyzer_port_counter' )",
            },
            "unsubscribe"=>{
                        :desc       =>"unsubscribe: -Removes a subscription",
                        :usage      =>"Stc.unsubscribe( resultDataSetHandle )",
                        :example    =>"Stc.unsubscribe( resultDataSet1 )",
            },
        }
    end
end



