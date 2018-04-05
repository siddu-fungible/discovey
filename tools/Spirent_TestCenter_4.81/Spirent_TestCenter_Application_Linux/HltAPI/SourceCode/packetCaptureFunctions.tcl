# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::packetCapture {

variable capture_PduList

# ACCookieTag
set capture_PduList(accookietag)                      accookietag
set capture_PduList(accookietag,stc)                  pppoe:ACCookieTag
set capture_PduList(accookietag,value)           "value"
set capture_PduList(accookietag,value,verify)      "none"
set capture_PduList(accookietag,length)          "length"
set capture_PduList(accookietag,length,verify)      "none"
set capture_PduList(accookietag,type)            "type"
set capture_PduList(accookietag,type,verify)      "none"
set capture_PduList(accookietag,all) {value length type}

# ACNameTag
set capture_PduList(acnametag)                      acnametag
set capture_PduList(acnametag,stc)                  pppoe:ACNameTag
set capture_PduList(acnametag,value)           "value"
set capture_PduList(acnametag,value,verify)      "none"
set capture_PduList(acnametag,length)          "length"
set capture_PduList(acnametag,length,verify)      "none"
set capture_PduList(acnametag,type)            "type"
set capture_PduList(acnametag,type,verify)      "none"
set capture_PduList(acnametag,all) {value length type}

# ACSystemErrorTag
set capture_PduList(acsystemerrortag)                      acsystemerrortag
set capture_PduList(acsystemerrortag,stc)                  pppoe:ACSystemErrorTag
set capture_PduList(acsystemerrortag,value)           "value"
set capture_PduList(acsystemerrortag,value,verify)      "none"
set capture_PduList(acsystemerrortag,length)          "length"
set capture_PduList(acsystemerrortag,length,verify)      "none"
set capture_PduList(acsystemerrortag,type)            "type"
set capture_PduList(acsystemerrortag,type,verify)      "none"
set capture_PduList(acsystemerrortag,all) {value length type}

# ARP
set capture_PduList(arp)                      arp
set capture_PduList(arp,stc)                  arp:ARP
set capture_PduList(arp,senderhwaddr)         "senderhwaddr"
set capture_PduList(arp,senderhwaddr,verify)  "mac"
set capture_PduList(arp,ipaddr)               "ipaddr"
set capture_PduList(arp,ipaddr,verify)        "int"
set capture_PduList(arp,senderpaddr)          "senderpaddr"
set capture_PduList(arp,senderpaddr,verify)   "ip"
set capture_PduList(arp,hardware)             "hardware"
set capture_PduList(arp,hardware,verify)      "hex"
set capture_PduList(arp,protocol)             "protocol"
set capture_PduList(arp,protocol,verify)      "hex"
set capture_PduList(arp,ihaddr)               "ihaddr"
set capture_PduList(arp,ihaddr,verify)        "int"
set capture_PduList(arp,operation)            "operation"
set capture_PduList(arp,operation,verify)     "int"
set capture_PduList(arp,targethwaddr)         "targethwaddr"
set capture_PduList(arp,targethwaddr,verify)  "mac"
set capture_PduList(arp,targetpaddr)          "targetpaddr"
set capture_PduList(arp,targetpaddr,verify)   "ip"
set capture_PduList(arp,all) {senderhwaddr ipaddr senderpaddr hardware protocol ihaddr operation targethwaddr targetpaddr}

# ATM
set capture_PduList(atm)                      atm
set capture_PduList(atm,stc)                  atm:ATM
set capture_PduList(atm,clp)             "clp"
set capture_PduList(atm,clp,verify)      "none"
set capture_PduList(atm,vpi)             "vpi"
set capture_PduList(atm,vpi,verify)      "none"
set capture_PduList(atm,vci)             "vci"
set capture_PduList(atm,vci,verify)      "none"
set capture_PduList(atm,all) {clp vpi vci}

# AuthSelect
set capture_PduList(authselect)                      authselect
set capture_PduList(authselect,stc)                  ospfv2:AuthSelect
set capture_PduList(authselect,all) {}

# CiscoHDLC
set capture_PduList(ciscohdlc)                      ciscohdlc
set capture_PduList(ciscohdlc,stc)                  hdlc:CiscoHDLC
set capture_PduList(ciscohdlc,protocoltype)    "protocoltype"
set capture_PduList(ciscohdlc,protocoltype,verify)      "none"
set capture_PduList(ciscohdlc,control)         "control"
set capture_PduList(ciscohdlc,control,verify)      "none"
set capture_PduList(ciscohdlc,address)         "address"
set capture_PduList(ciscohdlc,address,verify)      "none"
set capture_PduList(ciscohdlc,all) {protocoltype control address}

# ControlFlags
set capture_PduList(controlflags)                      controlflags
set capture_PduList(controlflags,stc)                  ipv4:ControlFlags
set capture_PduList(controlflags,reserved)        "reserved"
set capture_PduList(controlflags,reserved,verify)      "none"
set capture_PduList(controlflags,dfbit)           "dfbit"
set capture_PduList(controlflags,dfbit,verify)      "none"
set capture_PduList(controlflags,mfbit)           "mfbit"
set capture_PduList(controlflags,mfbit,verify)      "none"
set capture_PduList(controlflags,all) {reserved dfbit mfbit}

# Custom
set capture_PduList(custom)                      custom
set capture_PduList(custom,stc)                  custom:Custom
set capture_PduList(custom,pattern)         "pattern"
set capture_PduList(custom,pattern,verify)      "none"
set capture_PduList(custom,all) {pattern}

# DHCPClientIdHWTag
set capture_PduList(dhcpclientidhwtag)                      dhcpclientidhwtag
set capture_PduList(dhcpclientidhwtag,stc)                  dhcp:DHCPClientIdHWTag
set capture_PduList(dhcpclientidhwtag,clienthwa)       "clienthwa"
set capture_PduList(dhcpclientidhwtag,clienthwa,verify)      "none"
set capture_PduList(dhcpclientidhwtag,idtype)          "idtype"
set capture_PduList(dhcpclientidhwtag,idtype,verify)      "none"
set capture_PduList(dhcpclientidhwtag,optionlength)    "optionlength"
set capture_PduList(dhcpclientidhwtag,optionlength,verify)      "none"
set capture_PduList(dhcpclientidhwtag,type)            "type"
set capture_PduList(dhcpclientidhwtag,type,verify)      "none"
set capture_PduList(dhcpclientidhwtag,all) {clienthwa idtype optionlength type}

# DHCPClientIdnonHWTag
set capture_PduList(dhcpclientidnonhwtag)                      dhcpclientidnonhwtag
set capture_PduList(dhcpclientidnonhwtag,stc)                  dhcp:DHCPClientIdnonHWTag
set capture_PduList(dhcpclientidnonhwtag,idtype)          "idtype"
set capture_PduList(dhcpclientidnonhwtag,idtype,verify)      "none"
set capture_PduList(dhcpclientidnonhwtag,optionlength)    "optionlength"
set capture_PduList(dhcpclientidnonhwtag,optionlength,verify)      "none"
set capture_PduList(dhcpclientidnonhwtag,value)           "value"
set capture_PduList(dhcpclientidnonhwtag,value,verify)      "none"
set capture_PduList(dhcpclientidnonhwtag,type)            "type"
set capture_PduList(dhcpclientidnonhwtag,type,verify)      "none"
set capture_PduList(dhcpclientidnonhwtag,all) {idtype optionlength value type}

# Dhcpclientmsg
set capture_PduList(dhcpclientmsg)                      dhcpclientmsg
set capture_PduList(dhcpclientmsg,stc)                  dhcp:Dhcpclientmsg
set capture_PduList(dhcpclientmsg,clienthwpad)     "clienthwpad"
set capture_PduList(dhcpclientmsg,clienthwpad,verify)      "none"
set capture_PduList(dhcpclientmsg,bootfilename)    "bootfilename"
set capture_PduList(dhcpclientmsg,bootfilename,verify)      "none"
set capture_PduList(dhcpclientmsg,xid)             "xid"
set capture_PduList(dhcpclientmsg,xid,verify)      "none"
set capture_PduList(dhcpclientmsg,serverhostname)  "serverhostname"
set capture_PduList(dhcpclientmsg,serverhostname,verify)      "none"
set capture_PduList(dhcpclientmsg,messagetype)     "messagetype"
set capture_PduList(dhcpclientmsg,messagetype,verify)      "none"
set capture_PduList(dhcpclientmsg,clientmac)       "clientmac"
set capture_PduList(dhcpclientmsg,clientmac,verify)      "none"
set capture_PduList(dhcpclientmsg,hardwaretype)    "hardwaretype"
set capture_PduList(dhcpclientmsg,hardwaretype,verify)      "none"
set capture_PduList(dhcpclientmsg,nextservaddr)    "nextservaddr"
set capture_PduList(dhcpclientmsg,nextservaddr,verify)      "none"
set capture_PduList(dhcpclientmsg,haddrlen)        "haddrlen"
set capture_PduList(dhcpclientmsg,haddrlen,verify)      "none"
set capture_PduList(dhcpclientmsg,hops)            "hops"
set capture_PduList(dhcpclientmsg,hops,verify)      "none"
set capture_PduList(dhcpclientmsg,magiccookie)     "magiccookie"
set capture_PduList(dhcpclientmsg,magiccookie,verify)      "none"
set capture_PduList(dhcpclientmsg,elapsed)         "elapsed"
set capture_PduList(dhcpclientmsg,elapsed,verify)      "none"
set capture_PduList(dhcpclientmsg,relayagentaddr)  "relayagentaddr"
set capture_PduList(dhcpclientmsg,relayagentaddr,verify)      "none"
set capture_PduList(dhcpclientmsg,bootpflags)      "bootpflags"
set capture_PduList(dhcpclientmsg,bootpflags,verify)      "none"
set capture_PduList(dhcpclientmsg,clientaddr)      "clientaddr"
set capture_PduList(dhcpclientmsg,clientaddr,verify)      "none"
set capture_PduList(dhcpclientmsg,youraddr)        "youraddr"
set capture_PduList(dhcpclientmsg,youraddr,verify)      "none"
set capture_PduList(dhcpclientmsg,all) {clienthwpad bootfilename xid serverhostname messagetype clientmac hardwaretype nextservaddr haddrlen hops magiccookie elapsed relayagentaddr bootpflags clientaddr youraddr}

# DHCPcustomOptionTag
set capture_PduList(dhcpcustomoptiontag)                      dhcpcustomoptiontag
set capture_PduList(dhcpcustomoptiontag,stc)                  dhcp:DHCPcustomOptionTag
set capture_PduList(dhcpcustomoptiontag,value)           "value"
set capture_PduList(dhcpcustomoptiontag,value,verify)      "none"
set capture_PduList(dhcpcustomoptiontag,length)          "length"
set capture_PduList(dhcpcustomoptiontag,length,verify)      "none"
set capture_PduList(dhcpcustomoptiontag,type)            "type"
set capture_PduList(dhcpcustomoptiontag,type,verify)      "none"
set capture_PduList(dhcpcustomoptiontag,all) {value length type}

# DHCPHostNameTag
set capture_PduList(dhcphostnametag)                      dhcphostnametag
set capture_PduList(dhcphostnametag,stc)                  dhcp:DHCPHostNameTag
set capture_PduList(dhcphostnametag,value)           "value"
set capture_PduList(dhcphostnametag,value,verify)      "none"
set capture_PduList(dhcphostnametag,length)          "length"
set capture_PduList(dhcphostnametag,length,verify)      "none"
set capture_PduList(dhcphostnametag,type)            "type"
set capture_PduList(dhcphostnametag,type,verify)      "none"
set capture_PduList(dhcphostnametag,all) {value length type}

# DHCPleaseTimeTag
set capture_PduList(dhcpleasetimetag)                      dhcpleasetimetag
set capture_PduList(dhcpleasetimetag,stc)                  dhcp:DHCPleaseTimeTag
set capture_PduList(dhcpleasetimetag,leasetime)       "leasetime"
set capture_PduList(dhcpleasetimetag,leasetime,verify)      "none"
set capture_PduList(dhcpleasetimetag,length)          "length"
set capture_PduList(dhcpleasetimetag,length,verify)      "none"
set capture_PduList(dhcpleasetimetag,type)            "type"
set capture_PduList(dhcpleasetimetag,type,verify)      "none"
set capture_PduList(dhcpleasetimetag,all) {leasetime length type}

# DHCPMessageSizeTag
set capture_PduList(dhcpmessagesizetag)                      dhcpmessagesizetag
set capture_PduList(dhcpmessagesizetag,stc)                  dhcp:DHCPMessageSizeTag
set capture_PduList(dhcpmessagesizetag,value)           "value"
set capture_PduList(dhcpmessagesizetag,value,verify)      "none"
set capture_PduList(dhcpmessagesizetag,length)          "length"
set capture_PduList(dhcpmessagesizetag,length,verify)      "none"
set capture_PduList(dhcpmessagesizetag,type)            "type"
set capture_PduList(dhcpmessagesizetag,type,verify)      "none"
set capture_PduList(dhcpmessagesizetag,all) {value length type}

# DHCPmessageTag
set capture_PduList(dhcpmessagetag)                      dhcpmessagetag
set capture_PduList(dhcpmessagetag,stc)                  dhcp:DHCPmessageTag
set capture_PduList(dhcpmessagetag,value)           "value"
set capture_PduList(dhcpmessagetag,value,verify)      "none"
set capture_PduList(dhcpmessagetag,length)          "length"
set capture_PduList(dhcpmessagetag,length,verify)      "none"
set capture_PduList(dhcpmessagetag,type)            "type"
set capture_PduList(dhcpmessagetag,type,verify)      "none"
set capture_PduList(dhcpmessagetag,all) {value length type}

# DHCPMessageTypeTag
set capture_PduList(dhcpmessagetypetag)                      dhcpmessagetypetag
set capture_PduList(dhcpmessagetypetag,stc)                  dhcp:DHCPMessageTypeTag
set capture_PduList(dhcpmessagetypetag,code)            "code"
set capture_PduList(dhcpmessagetypetag,code,verify)      "none"
set capture_PduList(dhcpmessagetypetag,length)          "length"
set capture_PduList(dhcpmessagetypetag,length,verify)      "none"
set capture_PduList(dhcpmessagetypetag,type)            "type"
set capture_PduList(dhcpmessagetypetag,type,verify)      "none"
set capture_PduList(dhcpmessagetypetag,all) {code length type}

# DHCPOption
set capture_PduList(dhcpoption)                      dhcpoption
set capture_PduList(dhcpoption,stc)                  dhcp:DHCPOption
set capture_PduList(dhcpoption,all) {}

# DHCPOptionsList
set capture_PduList(dhcpoptionslist)                      dhcpoptionslist
set capture_PduList(dhcpoptionslist,stc)                  dhcp:DHCPOptionsList
set capture_PduList(dhcpoptionslist,all) {}

# DHCPoptOverloadTag
set capture_PduList(dhcpoptoverloadtag)                      dhcpoptoverloadtag
set capture_PduList(dhcpoptoverloadtag,stc)                  dhcp:DHCPoptOverloadTag
set capture_PduList(dhcpoptoverloadtag,overload)        "overload"
set capture_PduList(dhcpoptoverloadtag,overload,verify)      "none"
set capture_PduList(dhcpoptoverloadtag,length)          "length"
set capture_PduList(dhcpoptoverloadtag,length,verify)      "none"
set capture_PduList(dhcpoptoverloadtag,type)            "type"
set capture_PduList(dhcpoptoverloadtag,type,verify)      "none"
set capture_PduList(dhcpoptoverloadtag,all) {overload length type}

# DHCPReqAddrTag
set capture_PduList(dhcpreqaddrtag)                      dhcpreqaddrtag
set capture_PduList(dhcpreqaddrtag,stc)                  dhcp:DHCPReqAddrTag
set capture_PduList(dhcpreqaddrtag,reqaddr)         "reqaddr"
set capture_PduList(dhcpreqaddrtag,reqaddr,verify)      "none"
set capture_PduList(dhcpreqaddrtag,length)          "length"
set capture_PduList(dhcpreqaddrtag,length,verify)      "none"
set capture_PduList(dhcpreqaddrtag,type)            "type"
set capture_PduList(dhcpreqaddrtag,type,verify)      "none"
set capture_PduList(dhcpreqaddrtag,all) {reqaddr length type}

# DHCPReqParamTag
set capture_PduList(dhcpreqparamtag)                      dhcpreqparamtag
set capture_PduList(dhcpreqparamtag,stc)                  dhcp:DHCPReqParamTag
set capture_PduList(dhcpreqparamtag,value)           "value"
set capture_PduList(dhcpreqparamtag,value,verify)      "none"
set capture_PduList(dhcpreqparamtag,length)          "length"
set capture_PduList(dhcpreqparamtag,length,verify)      "none"
set capture_PduList(dhcpreqparamtag,type)            "type"
set capture_PduList(dhcpreqparamtag,type,verify)      "none"
set capture_PduList(dhcpreqparamtag,all) {value length type}

# DHCPserverIdTag
set capture_PduList(dhcpserveridtag)                      dhcpserveridtag
set capture_PduList(dhcpserveridtag,stc)                  dhcp:DHCPserverIdTag
set capture_PduList(dhcpserveridtag,reqaddr)         "reqaddr"
set capture_PduList(dhcpserveridtag,reqaddr,verify)      "none"
set capture_PduList(dhcpserveridtag,length)          "length"
set capture_PduList(dhcpserveridtag,length,verify)      "none"
set capture_PduList(dhcpserveridtag,type)            "type"
set capture_PduList(dhcpserveridtag,type,verify)      "none"
set capture_PduList(dhcpserveridtag,all) {reqaddr length type}

# Dhcpservermsg
set capture_PduList(dhcpservermsg)                      dhcpservermsg
set capture_PduList(dhcpservermsg,stc)                  dhcp:Dhcpservermsg
set capture_PduList(dhcpservermsg,clienthwpad)     "clienthwpad"
set capture_PduList(dhcpservermsg,clienthwpad,verify)      "none"
set capture_PduList(dhcpservermsg,bootfilename)    "bootfilename"
set capture_PduList(dhcpservermsg,bootfilename,verify)      "none"
set capture_PduList(dhcpservermsg,xid)             "xid"
set capture_PduList(dhcpservermsg,xid,verify)      "none"
set capture_PduList(dhcpservermsg,serverhostname)  "serverhostname"
set capture_PduList(dhcpservermsg,serverhostname,verify)      "none"
set capture_PduList(dhcpservermsg,messagetype)     "messagetype"
set capture_PduList(dhcpservermsg,messagetype,verify)      "none"
set capture_PduList(dhcpservermsg,clientmac)       "clientmac"
set capture_PduList(dhcpservermsg,clientmac,verify)      "none"
set capture_PduList(dhcpservermsg,hardwaretype)    "hardwaretype"
set capture_PduList(dhcpservermsg,hardwaretype,verify)      "none"
set capture_PduList(dhcpservermsg,nextservaddr)    "nextservaddr"
set capture_PduList(dhcpservermsg,nextservaddr,verify)      "none"
set capture_PduList(dhcpservermsg,haddrlen)        "haddrlen"
set capture_PduList(dhcpservermsg,haddrlen,verify)      "none"
set capture_PduList(dhcpservermsg,hops)            "hops"
set capture_PduList(dhcpservermsg,hops,verify)      "none"
set capture_PduList(dhcpservermsg,magiccookie)     "magiccookie"
set capture_PduList(dhcpservermsg,magiccookie,verify)      "none"
set capture_PduList(dhcpservermsg,elapsed)         "elapsed"
set capture_PduList(dhcpservermsg,elapsed,verify)      "none"
set capture_PduList(dhcpservermsg,relayagentaddr)  "relayagentaddr"
set capture_PduList(dhcpservermsg,relayagentaddr,verify)      "none"
set capture_PduList(dhcpservermsg,bootpflags)      "bootpflags"
set capture_PduList(dhcpservermsg,bootpflags,verify)      "none"
set capture_PduList(dhcpservermsg,clientaddr)      "clientaddr"
set capture_PduList(dhcpservermsg,clientaddr,verify)      "none"
set capture_PduList(dhcpservermsg,youraddr)        "youraddr"
set capture_PduList(dhcpservermsg,youraddr,verify)      "none"
set capture_PduList(dhcpservermsg,all) {clienthwpad bootfilename xid serverhostname messagetype clientmac hardwaretype nextservaddr haddrlen hops magiccookie elapsed relayagentaddr bootpflags clientaddr youraddr}

# DiffServByte
set capture_PduList(diffservbyte)                      diffservbyte
set capture_PduList(diffservbyte,stc)                  ipv4:DiffServByte
set capture_PduList(diffservbyte,reserved)        "reserved"
set capture_PduList(diffservbyte,reserved,verify)      "none"
set capture_PduList(diffservbyte,dscplow)         "dscplow"
set capture_PduList(diffservbyte,dscplow,verify)      "none"
set capture_PduList(diffservbyte,dscphigh)        "dscphigh"
set capture_PduList(diffservbyte,dscphigh,verify)      "none"
set capture_PduList(diffservbyte,all) {reserved dscplow dscphigh}

# EncodedGroupIpv4Address
set capture_PduList(encodedgroupipv4address)                      encodedgroupipv4address
set capture_PduList(encodedgroupipv4address,stc)                  pim:EncodedGroupIpv4Address
set capture_PduList(encodedgroupipv4address,masklen)         "masklen"
set capture_PduList(encodedgroupipv4address,masklen,verify)      "none"
set capture_PduList(encodedgroupipv4address,reserved)        "reserved"
set capture_PduList(encodedgroupipv4address,reserved,verify)      "none"
set capture_PduList(encodedgroupipv4address,zbit)            "zbit"
set capture_PduList(encodedgroupipv4address,zbit,verify)      "none"
set capture_PduList(encodedgroupipv4address,bbit)            "bbit"
set capture_PduList(encodedgroupipv4address,bbit,verify)      "none"
set capture_PduList(encodedgroupipv4address,encodingtype)    "encodingtype"
set capture_PduList(encodedgroupipv4address,encodingtype,verify)      "none"
set capture_PduList(encodedgroupipv4address,addrfamily)      "addrfamily"
set capture_PduList(encodedgroupipv4address,addrfamily,verify)      "none"
set capture_PduList(encodedgroupipv4address,address)         "address"
set capture_PduList(encodedgroupipv4address,address,verify)      "none"
set capture_PduList(encodedgroupipv4address,all) {masklen reserved zbit bbit encodingtype addrfamily address}

# EncodedGroupIpv6Address
set capture_PduList(encodedgroupipv6address)                      encodedgroupipv6address
set capture_PduList(encodedgroupipv6address,stc)                  pim:EncodedGroupIpv6Address
set capture_PduList(encodedgroupipv6address,masklen)         "masklen"
set capture_PduList(encodedgroupipv6address,masklen,verify)      "none"
set capture_PduList(encodedgroupipv6address,reserved)        "reserved"
set capture_PduList(encodedgroupipv6address,reserved,verify)      "none"
set capture_PduList(encodedgroupipv6address,zbit)            "zbit"
set capture_PduList(encodedgroupipv6address,zbit,verify)      "none"
set capture_PduList(encodedgroupipv6address,bbit)            "bbit"
set capture_PduList(encodedgroupipv6address,bbit,verify)      "none"
set capture_PduList(encodedgroupipv6address,encodingtype)    "encodingtype"
set capture_PduList(encodedgroupipv6address,encodingtype,verify)      "none"
set capture_PduList(encodedgroupipv6address,addrfamily)      "addrfamily"
set capture_PduList(encodedgroupipv6address,addrfamily,verify)      "none"
set capture_PduList(encodedgroupipv6address,address)         "address"
set capture_PduList(encodedgroupipv6address,address,verify)      "none"
set capture_PduList(encodedgroupipv6address,all) {masklen reserved zbit bbit encodingtype addrfamily address}

# EncodedSourceIpv4Address
set capture_PduList(encodedsourceipv4address)                      encodedsourceipv4address
set capture_PduList(encodedsourceipv4address,stc)                  pim:EncodedSourceIpv4Address
set capture_PduList(encodedsourceipv4address,encoding-type)   "encoding-type"
set capture_PduList(encodedsourceipv4address,encoding-type,verify)      "none"
set capture_PduList(encodedsourceipv4address,wbit)            "wbit"
set capture_PduList(encodedsourceipv4address,wbit,verify)      "none"
set capture_PduList(encodedsourceipv4address,address)         "address"
set capture_PduList(encodedsourceipv4address,address,verify)      "none"
set capture_PduList(encodedsourceipv4address,rbit)            "rbit"
set capture_PduList(encodedsourceipv4address,rbit,verify)      "none"
set capture_PduList(encodedsourceipv4address,masklen)         "masklen"
set capture_PduList(encodedsourceipv4address,masklen,verify)      "none"
set capture_PduList(encodedsourceipv4address,addrfamily)      "addrfamily"
set capture_PduList(encodedsourceipv4address,addrfamily,verify)      "none"
set capture_PduList(encodedsourceipv4address,reserved)        "reserved"
set capture_PduList(encodedsourceipv4address,reserved,verify)      "none"
set capture_PduList(encodedsourceipv4address,sbit)            "sbit"
set capture_PduList(encodedsourceipv4address,sbit,verify)      "none"
set capture_PduList(encodedsourceipv4address,all) {encoding-type wbit address rbit masklen addrfamily reserved sbit}

# EncodedSourceIpv6Address
set capture_PduList(encodedsourceipv6address)                      encodedsourceipv6address
set capture_PduList(encodedsourceipv6address,stc)                  pim:EncodedSourceIpv6Address
set capture_PduList(encodedsourceipv6address,encoding-type)   "encoding-type"
set capture_PduList(encodedsourceipv6address,encoding-type,verify)      "none"
set capture_PduList(encodedsourceipv6address,wbit)            "wbit"
set capture_PduList(encodedsourceipv6address,wbit,verify)      "none"
set capture_PduList(encodedsourceipv6address,address)         "address"
set capture_PduList(encodedsourceipv6address,address,verify)      "none"
set capture_PduList(encodedsourceipv6address,rbit)            "rbit"
set capture_PduList(encodedsourceipv6address,rbit,verify)      "none"
set capture_PduList(encodedsourceipv6address,masklen)         "masklen"
set capture_PduList(encodedsourceipv6address,masklen,verify)      "none"
set capture_PduList(encodedsourceipv6address,addrfamily)      "addrfamily"
set capture_PduList(encodedsourceipv6address,addrfamily,verify)      "none"
set capture_PduList(encodedsourceipv6address,reserved)        "reserved"
set capture_PduList(encodedsourceipv6address,reserved,verify)      "none"
set capture_PduList(encodedsourceipv6address,sbit)            "sbit"
set capture_PduList(encodedsourceipv6address,sbit,verify)      "none"
set capture_PduList(encodedsourceipv6address,all) {encoding-type wbit address rbit masklen addrfamily reserved sbit}

# EncodedUnicastIpv4Address
set capture_PduList(encodedunicastipv4address)                      encodedunicastipv4address
set capture_PduList(encodedunicastipv4address,stc)                  pim:EncodedUnicastIpv4Address
set capture_PduList(encodedunicastipv4address,encodingtype)    "encodingtype"
set capture_PduList(encodedunicastipv4address,encodingtype,verify)      "none"
set capture_PduList(encodedunicastipv4address,addrfamily)      "addrfamily"
set capture_PduList(encodedunicastipv4address,addrfamily,verify)      "none"
set capture_PduList(encodedunicastipv4address,address)         "address"
set capture_PduList(encodedunicastipv4address,address,verify)      "none"
set capture_PduList(encodedunicastipv4address,all) {encodingtype addrfamily address}

# EncodedUnicastIpv6Address
set capture_PduList(encodedunicastipv6address)                      encodedunicastipv6address
set capture_PduList(encodedunicastipv6address,stc)                  pim:EncodedUnicastIpv6Address
set capture_PduList(encodedunicastipv6address,encodingtype)    "encodingtype"
set capture_PduList(encodedunicastipv6address,encodingtype,verify)      "none"
set capture_PduList(encodedunicastipv6address,addrfamily)      "addrfamily"
set capture_PduList(encodedunicastipv6address,addrfamily,verify)      "none"
set capture_PduList(encodedunicastipv6address,address)         "address"
set capture_PduList(encodedunicastipv6address,address,verify)      "none"
set capture_PduList(encodedunicastipv6address,all) {encodingtype addrfamily address}

# EndOfListTag
set capture_PduList(endoflisttag)                      endoflisttag
set capture_PduList(endoflisttag,stc)                  pppoe:EndOfListTag
set capture_PduList(endoflisttag,length)          "length"
set capture_PduList(endoflisttag,length,verify)      "none"
set capture_PduList(endoflisttag,type)            "type"
set capture_PduList(endoflisttag,type,verify)      "none"
set capture_PduList(endoflisttag,all) {length type}

# EndOfOptionsTag
set capture_PduList(endofoptionstag)                      endofoptionstag
set capture_PduList(endofoptionstag,stc)                  dhcp:EndOfOptionsTag
set capture_PduList(endofoptionstag,type)            "type"
set capture_PduList(endofoptionstag,type,verify)      "none"
set capture_PduList(endofoptionstag,all) {type}

# Ethernet8022
set capture_PduList(ethernet8022)                      ethernet8022
set capture_PduList(ethernet8022,stc)                  ethernet:Ethernet8022
set capture_PduList(ethernet8022,dstmac)          "dstmac"
set capture_PduList(ethernet8022,dstmac,verify)      "none"
set capture_PduList(ethernet8022,preamble)        "preamble"
set capture_PduList(ethernet8022,preamble,verify)      "none"
set capture_PduList(ethernet8022,srcmac)          "srcmac"
set capture_PduList(ethernet8022,srcmac,verify)      "none"
set capture_PduList(ethernet8022,length)          "length"
set capture_PduList(ethernet8022,length,verify)      "none"
set capture_PduList(ethernet8022,all) {dstmac preamble srcmac length}

# Ethernet8023Raw
set capture_PduList(ethernet8023raw)                      ethernet8023raw
set capture_PduList(ethernet8023raw,stc)                  ethernet:Ethernet8023Raw
set capture_PduList(ethernet8023raw,dstmac)          "dstmac"
set capture_PduList(ethernet8023raw,dstmac,verify)      "none"
set capture_PduList(ethernet8023raw,preamble)        "preamble"
set capture_PduList(ethernet8023raw,preamble,verify)      "none"
set capture_PduList(ethernet8023raw,srcmac)          "srcmac"
set capture_PduList(ethernet8023raw,srcmac,verify)      "none"
set capture_PduList(ethernet8023raw,length)          "length"
set capture_PduList(ethernet8023raw,length,verify)      "none"
set capture_PduList(ethernet8023raw,all) {dstmac preamble srcmac length}

# EthernetII
set capture_PduList(ethernetii)                      ethernetii
set capture_PduList(ethernetii,stc)                  ethernet:EthernetII
set capture_PduList(ethernetii,dstmac)          "dstmac"
set capture_PduList(ethernetii,dstmac,verify)      "none"
set capture_PduList(ethernetii,preamble)        "preamble"
set capture_PduList(ethernetii,preamble,verify)      "none"
set capture_PduList(ethernetii,srcmac)          "srcmac"
set capture_PduList(ethernetii,srcmac,verify)      "none"
set capture_PduList(ethernetii,ethertype)       "ethertype"
set capture_PduList(ethernetii,ethertype,verify)      "none"
set capture_PduList(ethernetii,all) {dstmac preamble srcmac ethertype}

# EthernetSnap
set capture_PduList(ethernetsnap)                      ethernetsnap
set capture_PduList(ethernetsnap,stc)                  ethernet:EthernetSnap
set capture_PduList(ethernetsnap,dstmac)          "dstmac"
set capture_PduList(ethernetsnap,dstmac,verify)      "none"
set capture_PduList(ethernetsnap,preamble)        "preamble"
set capture_PduList(ethernetsnap,preamble,verify)      "none"
set capture_PduList(ethernetsnap,srcmac)          "srcmac"
set capture_PduList(ethernetsnap,srcmac,verify)      "none"
set capture_PduList(ethernetsnap,length)          "length"
set capture_PduList(ethernetsnap,length,verify)      "none"
set capture_PduList(ethernetsnap,all) {dstmac preamble srcmac length}

# GenericErrorTag
set capture_PduList(genericerrortag)                      genericerrortag
set capture_PduList(genericerrortag,stc)                  pppoe:GenericErrorTag
set capture_PduList(genericerrortag,value)           "value"
set capture_PduList(genericerrortag,value,verify)      "none"
set capture_PduList(genericerrortag,length)          "length"
set capture_PduList(genericerrortag,length,verify)      "none"
set capture_PduList(genericerrortag,type)            "type"
set capture_PduList(genericerrortag,type,verify)      "none"
set capture_PduList(genericerrortag,all) {value length type}

# Eoam
set capture_PduList(eoam_ccm)                      eoam_ccm
set capture_PduList(eoam_ccm,stc)                  EOAM:CCM
set capture_PduList(eoam_ccm,ccmintervalfield)          "CCMIntervalField"
set capture_PduList(eoam_ccm,ccmintervalfield,verify)      "none"
set capture_PduList(eoam_ccm,rdibit)        "RDIbit"
set capture_PduList(eoam_ccm,rdibit,verify)      "none"
set capture_PduList(eoam_ccm,sequencenumber)          "SequenceNumber"
set capture_PduList(eoam_ccm,sequencenumber,verify)      "none"
set capture_PduList(eoam_ccm,maepi)       "MAEPI"
set capture_PduList(eoam_ccm,maepi,verify)      "none"
set capture_PduList(eoam_ccm,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_ccm,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_ccm,opcode)          "opcode"
set capture_PduList(eoam_ccm,opcode,verify)      "none"
set capture_PduList(eoam_ccm,reserved)        "Reserved"
set capture_PduList(eoam_ccm,reserved,verify)      "none"
set capture_PduList(eoam_ccm,maid.mdnf)          "maid.mdnf"
set capture_PduList(eoam_ccm,maid.mdnf,verify)      "none"
set capture_PduList(eoam_ccm,maid.smaf)        "maid.smaf"
set capture_PduList(eoam_ccm,maid.smaf,verify)      "none"
set capture_PduList(eoam_ccm,maid.smal)          "maid.smal"
set capture_PduList(eoam_ccm,maid.smal,verify)      "none"
set capture_PduList(eoam_ccm,maid.sman)       "maid.sman"
set capture_PduList(eoam_ccm,maid.sman,verify)      "none"
set capture_PduList(eoam_ccm,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_ccm,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_ccm,cfmheader.version)          "version"
set capture_PduList(eoam_ccm,cfmheader.version,verify)      "none"
set capture_PduList(eoam_ccm,macpreamble.dstmac)          "dstmac"
set capture_PduList(eoam_ccm,macpreamble.dstmac,verify)      "none"
set capture_PduList(eoam_ccm,macpreamble.srcmac)          "srcmac"
set capture_PduList(eoam_ccm,macpreamble.srcmac,verify)      "none"
set capture_PduList(eoam_ccm,macpreamble.ethertype)          "ethertype"
set capture_PduList(eoam_ccm,macpreamble.ethertype,verify)      "none"
set capture_PduList(eoam_ccm,all) {ccmintervalfield rdibit sequencenumber maepi firsttlvoffset opcode reserved maid.mdnf maid.smaf maid.smal maid.sman cfmheader.mdlevel cfmheader.version macpreamble.dstmac macpreamble.srcmac macpreamble.ethertype}

set capture_PduList(eoam_lbm)                      eoam_lbm
set capture_PduList(eoam_lbm,stc)                  EOAM:LBM
set capture_PduList(eoam_lbm,lbtid)          "lbtid"
set capture_PduList(eoam_lbm,lbtid,verify)      "none"
set capture_PduList(eoam_lbm,flags)        "flags"
set capture_PduList(eoam_lbm,flags,verify)      "none"
set capture_PduList(eoam_lbm,opcode)          "opcode"
set capture_PduList(eoam_lbm,opcode,verify)      "none"
set capture_PduList(eoam_lbm,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_lbm,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_lbm,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_lbm,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_lbm,cfmheader.version)          "version"
set capture_PduList(eoam_lbm,cfmheader.version,verify)      "none"
set capture_PduList(eoam_lbm,all) {lbtid flags opcode firsttlvoffset cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_lbr)                      eoam_lbr
set capture_PduList(eoam_lbr,stc)                  EOAM:LBR
set capture_PduList(eoam_lbr,lbtid)          "lbtid"
set capture_PduList(eoam_lbr,lbtid,verify)      "none"
set capture_PduList(eoam_lbr,flags)        "flags"
set capture_PduList(eoam_lbr,flags,verify)      "none"
set capture_PduList(eoam_lbr,opcode)          "opcode"
set capture_PduList(eoam_lbr,opcode,verify)      "none"
set capture_PduList(eoam_lbr,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_lbr,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_lbr,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_lbr,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_lbr,cfmheader.version)          "version"
set capture_PduList(eoam_lbr,cfmheader.version,verify)      "none"
set capture_PduList(eoam_lbr,all) {lbtid flags opcode firsttlvoffset cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_ltm)                      eoam_ltm
set capture_PduList(eoam_ltm,stc)                  EOAM:LTM
set capture_PduList(eoam_ltm,ltmtransid)          "LTMTransID"
set capture_PduList(eoam_ltm,ltmtransid,verify)      "none"
set capture_PduList(eoam_ltm,ltmttl)          "ltmttl"
set capture_PduList(eoam_ltm,ltmttl,verify)      "none"
set capture_PduList(eoam_ltm,flags)        "flags"
set capture_PduList(eoam_ltm,flags,verify)      "none"
set capture_PduList(eoam_ltm,opcode)          "opcode"
set capture_PduList(eoam_ltm,opcode,verify)      "none"
set capture_PduList(eoam_ltm,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_ltm,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_ltm,origmac)       "OrigMAC"
set capture_PduList(eoam_ltm,origmac,verify)      "none"
set capture_PduList(eoam_ltm,targetmac)       "TargetMAC"
set capture_PduList(eoam_ltm,targetmac,verify)      "none"
set capture_PduList(eoam_ltm,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_ltm,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_ltm,cfmheader.version)          "version"
set capture_PduList(eoam_ltm,cfmheader.version,verify)      "none"
set capture_PduList(eoam_ltm,all) {ltmtransid ltmttl flags opcode firsttlvoffset origmac targetmac cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_ltr)                      eoam_ltr
set capture_PduList(eoam_ltr,stc)                  EOAM:LTR
set capture_PduList(eoam_ltr,ltrtransid)          "LTRTransID"
set capture_PduList(eoam_ltr,ltrtransid,verify)      "none"
set capture_PduList(eoam_ltr,fwdyes)          "FwdYes"
set capture_PduList(eoam_ltr,fwdyes,verify)      "none"
set capture_PduList(eoam_ltr,reserved)        "Reserved"
set capture_PduList(eoam_ltr,reserved,verify)      "none"
set capture_PduList(eoam_ltr,opcode)          "opcode"
set capture_PduList(eoam_ltr,opcode,verify)      "none"
set capture_PduList(eoam_ltr,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_ltr,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_ltr,ltrrelayaction)       "ltrrelayaction"
set capture_PduList(eoam_ltr,ltrrelayaction,verify)      "none"
set capture_PduList(eoam_ltr,replyttl)       "ReplyTTL"
set capture_PduList(eoam_ltr,replyttl,verify)      "none"
set capture_PduList(eoam_ltr,termmep)       "termmep"
set capture_PduList(eoam_ltr,termmep,verify)      "none"
set capture_PduList(eoam_ltr,usefdbonly)       "usefdbonly"
set capture_PduList(eoam_ltr,usefdbonly,verify)      "none"
set capture_PduList(eoam_ltr,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_ltr,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_ltr,cfmheader.version)          "version"
set capture_PduList(eoam_ltr,cfmheader.version,verify)      "none"
set capture_PduList(eoam_ltr,all) {ltrtransid fwdyes reserved opcode firsttlvoffset ltrrelayaction replyttl termmep usefdbonly cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_dmm)                      eoam_dmm
set capture_PduList(eoam_dmm,stc)                  EOAM:DMM
set capture_PduList(eoam_dmm,flags)        "flags"
set capture_PduList(eoam_dmm,flags,verify)      "none"
set capture_PduList(eoam_dmm,opcode)          "opcode"
set capture_PduList(eoam_dmm,opcode,verify)      "none"
set capture_PduList(eoam_dmm,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_dmm,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_dmm,rxtimestampb)       "rxtimestampb"
set capture_PduList(eoam_dmm,rxtimestampb,verify)      "none"
set capture_PduList(eoam_dmm,rxtimestampf)       "RxTimeStampf"
set capture_PduList(eoam_dmm,rxtimestampf,verify)      "none"
set capture_PduList(eoam_dmm,txtimestampb)       "TxTimeStampb"
set capture_PduList(eoam_dmm,txtimestampb,verify)      "none"
set capture_PduList(eoam_dmm,txtimestampf)       "TxTimeStampf"
set capture_PduList(eoam_dmm,txtimestampf,verify)      "none"
set capture_PduList(eoam_dmm,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_dmm,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_dmm,cfmheader.version)          "version"
set capture_PduList(eoam_dmm,cfmheader.version,verify)      "none"
set capture_PduList(eoam_dmm,all) {flags opcode firsttlvoffset rxtimestampb rxtimestampf txtimestampb txtimestampf cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_dmr)                      eoam_dmr
set capture_PduList(eoam_dmr,stc)                  EOAM:DMR
set capture_PduList(eoam_dmr,flags)        "flags"
set capture_PduList(eoam_dmr,flags,verify)      "none"
set capture_PduList(eoam_dmr,opcode)          "opcode"
set capture_PduList(eoam_dmr,opcode,verify)      "none"
set capture_PduList(eoam_dmr,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_dmr,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_dmr,rxtimestampb)       "rxtimestampb"
set capture_PduList(eoam_dmr,rxtimestampb,verify)      "none"
set capture_PduList(eoam_dmr,rxtimestampf)       "RxTimeStampf"
set capture_PduList(eoam_dmr,rxtimestampf,verify)      "none"
set capture_PduList(eoam_dmr,txtimestampb)       "TxTimeStampb"
set capture_PduList(eoam_dmr,txtimestampb,verify)      "none"
set capture_PduList(eoam_dmr,txtimestampf)       "TxTimeStampf"
set capture_PduList(eoam_dmr,txtimestampf,verify)      "none"
set capture_PduList(eoam_dmr,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_dmr,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_dmr,cfmheader.version)          "version"
set capture_PduList(eoam_dmr,cfmheader.version,verify)      "none"
set capture_PduList(eoam_dmr,all) {flags opcode firsttlvoffset rxtimestampb rxtimestampf txtimestampb txtimestampf cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_lmm)                      eoam_lmm
set capture_PduList(eoam_lmm,stc)                  EOAM:LMM
set capture_PduList(eoam_lmm,flags)        "flags"
set capture_PduList(eoam_lmm,flags,verify)      "none"
set capture_PduList(eoam_lmm,opcode)          "opcode"
set capture_PduList(eoam_lmm,opcode,verify)      "none"
set capture_PduList(eoam_lmm,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_lmm,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_lmm,rxfcf)       "RxFCf"
set capture_PduList(eoam_lmm,rxfcf,verify)      "none"
set capture_PduList(eoam_lmm,txfcb)       "TxFCb"
set capture_PduList(eoam_lmm,txfcb,verify)      "none"
set capture_PduList(eoam_lmm,txfcf)       "TxFCf"
set capture_PduList(eoam_lmm,txfcf,verify)      "none"
set capture_PduList(eoam_lmm,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_lmm,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_lmm,cfmheader.version)          "version"
set capture_PduList(eoam_lmm,cfmheader.version,verify)      "none"
set capture_PduList(eoam_lmm,all) {flags opcode firsttlvoffset rxfcf txfcb txfcf cfmheader.mdlevel cfmheader.version}

set capture_PduList(eoam_lmr)                      eoam_lmr
set capture_PduList(eoam_lmr,stc)                  EOAM:LMR
set capture_PduList(eoam_lmr,flags)        "flags"
set capture_PduList(eoam_lmr,flags,verify)      "none"
set capture_PduList(eoam_lmr,opcode)          "opcode"
set capture_PduList(eoam_lmr,opcode,verify)      "none"
set capture_PduList(eoam_lmr,firsttlvoffset)       "firsttlvoffset"
set capture_PduList(eoam_lmr,firsttlvoffset,verify)      "none"
set capture_PduList(eoam_lmr,rxfcf)       "RxFCf"
set capture_PduList(eoam_lmr,rxfcf,verify)      "none"
set capture_PduList(eoam_lmr,txfcb)       "TxFCb"
set capture_PduList(eoam_lmr,txfcb,verify)      "none"
set capture_PduList(eoam_lmr,txfcf)       "TxFCf"
set capture_PduList(eoam_lmr,txfcf,verify)      "none"
set capture_PduList(eoam_lmr,cfmheader.mdlevel)          "mdlevel"
set capture_PduList(eoam_lmr,cfmheader.mdlevel,verify)      "none"
set capture_PduList(eoam_lmr,cfmheader.version)          "version"
set capture_PduList(eoam_lmr,cfmheader.version,verify)      "none"
set capture_PduList(eoam_lmr,all) {flags opcode firsttlvoffset rxfcf txfcb txfcf cfmheader.mdlevel cfmheader.version}


# Gre
set capture_PduList(gre)                      gre
set capture_PduList(gre,stc)                  gre:Gre
set capture_PduList(gre,version)         "version"
set capture_PduList(gre,version,verify)      "none"
set capture_PduList(gre,ckpresent)       "ckpresent"
set capture_PduList(gre,ckpresent,verify)      "none"
set capture_PduList(gre,reserved0)       "reserved0"
set capture_PduList(gre,reserved0,verify)      "none"
set capture_PduList(gre,routingpresent)  "routingpresent"
set capture_PduList(gre,routingpresent,verify)      "none"
set capture_PduList(gre,seqnumpresent)   "seqnumpresent"
set capture_PduList(gre,seqnumpresent,verify)      "none"
set capture_PduList(gre,endpointv4)      "endpointv4"
set capture_PduList(gre,endpointv4,verify)      "none"
set capture_PduList(gre,protocoltype)    "protocoltype"
set capture_PduList(gre,protocoltype,verify)      "none"
set capture_PduList(gre,endpointv6)      "endpointv6"
set capture_PduList(gre,endpointv6,verify)      "none"
set capture_PduList(gre,keypresent)      "keypresent"
set capture_PduList(gre,keypresent,verify)      "none"
set capture_PduList(gre,all) {version ckpresent reserved0 routingpresent seqnumpresent endpointv4 protocoltype endpointv6 keypresent}

# GreChecksum
set capture_PduList(grechecksum)                      grechecksum
set capture_PduList(grechecksum,stc)                  gre:GreChecksum
set capture_PduList(grechecksum,reserved)        "reserved"
set capture_PduList(grechecksum,reserved,verify)      "none"
set capture_PduList(grechecksum,value)           "value"
set capture_PduList(grechecksum,value,verify)      "none"
set capture_PduList(grechecksum,all) {reserved value}

# GreChecksumList
set capture_PduList(grechecksumlist)                      grechecksumlist
set capture_PduList(grechecksumlist,stc)                  gre:GreChecksumList
set capture_PduList(grechecksumlist,all) {}

# GreKey
set capture_PduList(grekey)                      grekey
set capture_PduList(grekey,stc)                  gre:GreKey
set capture_PduList(grekey,value)           "value"
set capture_PduList(grekey,value,verify)      "none"
set capture_PduList(grekey,all) {value}

# GreKeyList
set capture_PduList(grekeylist)                      grekeylist
set capture_PduList(grekeylist,stc)                  gre:GreKeyList
set capture_PduList(grekeylist,all) {}

# GreSeqNum
set capture_PduList(greseqnum)                      greseqnum
set capture_PduList(greseqnum,stc)                  gre:GreSeqNum
set capture_PduList(greseqnum,value)           "value"
set capture_PduList(greseqnum,value,verify)      "none"
set capture_PduList(greseqnum,all) {value}

# GreSeqNumList
set capture_PduList(greseqnumlist)                      greseqnumlist
set capture_PduList(greseqnumlist,stc)                  gre:GreSeqNumList
set capture_PduList(greseqnumlist,all) {}

# GroupRecord
set capture_PduList(grouprecord)                      grouprecord
set capture_PduList(grouprecord,stc)                  igmp:GroupRecord
set capture_PduList(grouprecord,mcastaddr)       "mcastaddr"
set capture_PduList(grouprecord,mcastaddr,verify)      "none"
set capture_PduList(grouprecord,auxdatalen)      "auxdatalen"
set capture_PduList(grouprecord,auxdatalen,verify)      "none"
set capture_PduList(grouprecord,numsource)       "numsource"
set capture_PduList(grouprecord,numsource,verify)      "none"
set capture_PduList(grouprecord,recordtype)      "recordtype"
set capture_PduList(grouprecord,recordtype,verify)      "none"
set capture_PduList(grouprecord,all) {mcastaddr auxdatalen numsource recordtype}

# GroupRecordList
set capture_PduList(grouprecordlist)                      grouprecordlist
set capture_PduList(grouprecordlist,stc)                  igmp:GroupRecordList
set capture_PduList(grouprecordlist,all) {}

# HdrAuthSelectCrypto
set capture_PduList(hdrauthselectcrypto)                      hdrauthselectcrypto
set capture_PduList(hdrauthselectcrypto,stc)                  ospfv2:HdrAuthSelectCrypto
set capture_PduList(hdrauthselectcrypto,authvalue1)      "authvalue1"
set capture_PduList(hdrauthselectcrypto,authvalue1,verify)      "none"
set capture_PduList(hdrauthselectcrypto,authtype)        "authtype"
set capture_PduList(hdrauthselectcrypto,authtype,verify)      "none"
set capture_PduList(hdrauthselectcrypto,authvalue2)      "authvalue2"
set capture_PduList(hdrauthselectcrypto,authvalue2,verify)      "none"
set capture_PduList(hdrauthselectcrypto,all) {authvalue1 authtype authvalue2}

# HdrAuthSelectNone
set capture_PduList(hdrauthselectnone)                      hdrauthselectnone
set capture_PduList(hdrauthselectnone,stc)                  ospfv2:HdrAuthSelectNone
set capture_PduList(hdrauthselectnone,authvalue1)      "authvalue1"
set capture_PduList(hdrauthselectnone,authvalue1,verify)      "none"
set capture_PduList(hdrauthselectnone,authtype)        "authtype"
set capture_PduList(hdrauthselectnone,authtype,verify)      "none"
set capture_PduList(hdrauthselectnone,authvalue2)      "authvalue2"
set capture_PduList(hdrauthselectnone,authvalue2,verify)      "none"
set capture_PduList(hdrauthselectnone,all) {authvalue1 authtype authvalue2}

# HdrAuthSelectPassword
set capture_PduList(hdrauthselectpassword)                      hdrauthselectpassword
set capture_PduList(hdrauthselectpassword,stc)                  ospfv2:HdrAuthSelectPassword
set capture_PduList(hdrauthselectpassword,authvalue1)      "authvalue1"
set capture_PduList(hdrauthselectpassword,authvalue1,verify)      "none"
set capture_PduList(hdrauthselectpassword,authtype)        "authtype"
set capture_PduList(hdrauthselectpassword,authtype,verify)      "none"
set capture_PduList(hdrauthselectpassword,authvalue2)      "authvalue2"
set capture_PduList(hdrauthselectpassword,authvalue2,verify)      "none"
set capture_PduList(hdrauthselectpassword,all) {authvalue1 authtype authvalue2}

# HdrAuthSelectUserDef
set capture_PduList(hdrauthselectuserdef)                      hdrauthselectuserdef
set capture_PduList(hdrauthselectuserdef,stc)                  ospfv2:HdrAuthSelectUserDef
set capture_PduList(hdrauthselectuserdef,authvalue1)      "authvalue1"
set capture_PduList(hdrauthselectuserdef,authvalue1,verify)      "none"
set capture_PduList(hdrauthselectuserdef,authtype)        "authtype"
set capture_PduList(hdrauthselectuserdef,authtype,verify)      "none"
set capture_PduList(hdrauthselectuserdef,authvalue2)      "authvalue2"
set capture_PduList(hdrauthselectuserdef,authvalue2,verify)      "none"
set capture_PduList(hdrauthselectuserdef,all) {authvalue1 authtype authvalue2}

# HostUniqTag
set capture_PduList(hostuniqtag)                      hostuniqtag
set capture_PduList(hostuniqtag,stc)                  pppoe:HostUniqTag
set capture_PduList(hostuniqtag,value)           "value"
set capture_PduList(hostuniqtag,value,verify)      "none"
set capture_PduList(hostuniqtag,length)          "length"
set capture_PduList(hostuniqtag,length,verify)      "none"
set capture_PduList(hostuniqtag,type)            "type"
set capture_PduList(hostuniqtag,type,verify)      "none"
set capture_PduList(hostuniqtag,all) {value length type}

# IcmpDestUnreach
set capture_PduList(icmpdestunreach)                      icmpdestunreach
set capture_PduList(icmpdestunreach,stc)                  icmp:IcmpDestUnreach
set capture_PduList(icmpdestunreach,checksum)        "checksum"
set capture_PduList(icmpdestunreach,checksum,verify)      "none"
set capture_PduList(icmpdestunreach,code)            "code"
set capture_PduList(icmpdestunreach,code,verify)      "none"
set capture_PduList(icmpdestunreach,unused)          "unused"
set capture_PduList(icmpdestunreach,unused,verify)      "none"
set capture_PduList(icmpdestunreach,type)            "type"
set capture_PduList(icmpdestunreach,type,verify)      "none"
set capture_PduList(icmpdestunreach,all) {checksum code unused type}

# IcmpEchoReply
set capture_PduList(icmpechoreply)                      icmpechoreply
set capture_PduList(icmpechoreply,stc)                  icmp:IcmpEchoReply
set capture_PduList(icmpechoreply,identifier)      "identifier"
set capture_PduList(icmpechoreply,identifier,verify)      "none"
set capture_PduList(icmpechoreply,checksum)        "checksum"
set capture_PduList(icmpechoreply,checksum,verify)      "none"
set capture_PduList(icmpechoreply,code)            "code"
set capture_PduList(icmpechoreply,code,verify)      "none"
set capture_PduList(icmpechoreply,seqnum)          "seqnum"
set capture_PduList(icmpechoreply,seqnum,verify)      "none"
set capture_PduList(icmpechoreply,data)            "data"
set capture_PduList(icmpechoreply,data,verify)      "none"
set capture_PduList(icmpechoreply,type)            "type"
set capture_PduList(icmpechoreply,type,verify)      "none"
set capture_PduList(icmpechoreply,all) {identifier checksum code seqnum data type}

# IcmpEchoRequest
set capture_PduList(icmpechorequest)                      icmpechorequest
set capture_PduList(icmpechorequest,stc)                  icmp:IcmpEchoRequest
set capture_PduList(icmpechorequest,identifier)      "identifier"
set capture_PduList(icmpechorequest,identifier,verify)      "none"
set capture_PduList(icmpechorequest,checksum)        "checksum"
set capture_PduList(icmpechorequest,checksum,verify)      "none"
set capture_PduList(icmpechorequest,code)            "code"
set capture_PduList(icmpechorequest,code,verify)      "none"
set capture_PduList(icmpechorequest,seqnum)          "seqnum"
set capture_PduList(icmpechorequest,seqnum,verify)      "none"
set capture_PduList(icmpechorequest,data)            "data"
set capture_PduList(icmpechorequest,data,verify)      "none"
set capture_PduList(icmpechorequest,type)            "type"
set capture_PduList(icmpechorequest,type,verify)      "none"
set capture_PduList(icmpechorequest,all) {identifier checksum code seqnum data type}

# IcmpInfoReply
set capture_PduList(icmpinforeply)                      icmpinforeply
set capture_PduList(icmpinforeply,stc)                  icmp:IcmpInfoReply
set capture_PduList(icmpinforeply,identifier)      "identifier"
set capture_PduList(icmpinforeply,identifier,verify)      "none"
set capture_PduList(icmpinforeply,checksum)        "checksum"
set capture_PduList(icmpinforeply,checksum,verify)      "none"
set capture_PduList(icmpinforeply,code)            "code"
set capture_PduList(icmpinforeply,code,verify)      "none"
set capture_PduList(icmpinforeply,seqnum)          "seqnum"
set capture_PduList(icmpinforeply,seqnum,verify)      "none"
set capture_PduList(icmpinforeply,type)            "type"
set capture_PduList(icmpinforeply,type,verify)      "none"
set capture_PduList(icmpinforeply,all) {identifier checksum code seqnum type}

# IcmpInfoRequest
set capture_PduList(icmpinforequest)                      icmpinforequest
set capture_PduList(icmpinforequest,stc)                  icmp:IcmpInfoRequest
set capture_PduList(icmpinforequest,identifier)      "identifier"
set capture_PduList(icmpinforequest,identifier,verify)      "none"
set capture_PduList(icmpinforequest,checksum)        "checksum"
set capture_PduList(icmpinforequest,checksum,verify)      "none"
set capture_PduList(icmpinforequest,code)            "code"
set capture_PduList(icmpinforequest,code,verify)      "none"
set capture_PduList(icmpinforequest,seqnum)          "seqnum"
set capture_PduList(icmpinforequest,seqnum,verify)      "none"
set capture_PduList(icmpinforequest,type)            "type"
set capture_PduList(icmpinforequest,type,verify)      "none"
set capture_PduList(icmpinforequest,all) {identifier checksum code seqnum type}

# IcmpIpData
set capture_PduList(icmpipdata)                      icmpipdata
set capture_PduList(icmpipdata,stc)                  icmp:IcmpIpData
set capture_PduList(icmpipdata,data)            "data"
set capture_PduList(icmpipdata,data,verify)      "none"
set capture_PduList(icmpipdata,all) {data}

# IcmpParameterProblem
set capture_PduList(icmpparameterproblem)                      icmpparameterproblem
set capture_PduList(icmpparameterproblem,stc)                  icmp:IcmpParameterProblem
set capture_PduList(icmpparameterproblem,checksum)        "checksum"
set capture_PduList(icmpparameterproblem,checksum,verify)      "none"
set capture_PduList(icmpparameterproblem,code)            "code"
set capture_PduList(icmpparameterproblem,code,verify)      "none"
set capture_PduList(icmpparameterproblem,unused)          "unused"
set capture_PduList(icmpparameterproblem,unused,verify)      "none"
set capture_PduList(icmpparameterproblem,pointer)         "pointer"
set capture_PduList(icmpparameterproblem,pointer,verify)      "none"
set capture_PduList(icmpparameterproblem,type)            "type"
set capture_PduList(icmpparameterproblem,type,verify)      "none"
set capture_PduList(icmpparameterproblem,all) {checksum code unused pointer type}

# IcmpRedirect
set capture_PduList(icmpredirect)                      icmpredirect
set capture_PduList(icmpredirect,stc)                  icmp:IcmpRedirect
set capture_PduList(icmpredirect,checksum)        "checksum"
set capture_PduList(icmpredirect,checksum,verify)      "none"
set capture_PduList(icmpredirect,code)            "code"
set capture_PduList(icmpredirect,code,verify)      "none"
set capture_PduList(icmpredirect,gateway)         "gateway"
set capture_PduList(icmpredirect,gateway,verify)      "none"
set capture_PduList(icmpredirect,type)            "type"
set capture_PduList(icmpredirect,type,verify)      "none"
set capture_PduList(icmpredirect,all) {checksum code gateway type}

# IcmpSourceQuench
set capture_PduList(icmpsourcequench)                      icmpsourcequench
set capture_PduList(icmpsourcequench,stc)                  icmp:IcmpSourceQuench
set capture_PduList(icmpsourcequench,checksum)        "checksum"
set capture_PduList(icmpsourcequench,checksum,verify)      "none"
set capture_PduList(icmpsourcequench,code)            "code"
set capture_PduList(icmpsourcequench,code,verify)      "none"
set capture_PduList(icmpsourcequench,unused)          "unused"
set capture_PduList(icmpsourcequench,unused,verify)      "none"
set capture_PduList(icmpsourcequench,type)            "type"
set capture_PduList(icmpsourcequench,type,verify)      "none"
set capture_PduList(icmpsourcequench,all) {checksum code unused type}

# IcmpTimeExceeded
set capture_PduList(icmptimeexceeded)                      icmptimeexceeded
set capture_PduList(icmptimeexceeded,stc)                  icmp:IcmpTimeExceeded
set capture_PduList(icmptimeexceeded,checksum)        "checksum"
set capture_PduList(icmptimeexceeded,checksum,verify)      "none"
set capture_PduList(icmptimeexceeded,code)            "code"
set capture_PduList(icmptimeexceeded,code,verify)      "none"
set capture_PduList(icmptimeexceeded,unused)          "unused"
set capture_PduList(icmptimeexceeded,unused,verify)      "none"
set capture_PduList(icmptimeexceeded,type)            "type"
set capture_PduList(icmptimeexceeded,type,verify)      "none"
set capture_PduList(icmptimeexceeded,all) {checksum code unused type}

# IcmpTimestampReply
set capture_PduList(icmptimestampreply)                      icmptimestampreply
set capture_PduList(icmptimestampreply,stc)                  icmp:IcmpTimestampReply
set capture_PduList(icmptimestampreply,code)            "code"
set capture_PduList(icmptimestampreply,code,verify)      "none"
set capture_PduList(icmptimestampreply,checksum)        "checksum"
set capture_PduList(icmptimestampreply,checksum,verify)      "none"
set capture_PduList(icmptimestampreply,transmit)        "transmit"
set capture_PduList(icmptimestampreply,transmit,verify)      "none"
set capture_PduList(icmptimestampreply,identifier)      "identifier"
set capture_PduList(icmptimestampreply,identifier,verify)      "none"
set capture_PduList(icmptimestampreply,receive)         "receive"
set capture_PduList(icmptimestampreply,receive,verify)      "none"
set capture_PduList(icmptimestampreply,seqnum)          "seqnum"
set capture_PduList(icmptimestampreply,seqnum,verify)      "none"
set capture_PduList(icmptimestampreply,type)            "type"
set capture_PduList(icmptimestampreply,type,verify)      "none"
set capture_PduList(icmptimestampreply,originate)       "originate"
set capture_PduList(icmptimestampreply,originate,verify)      "none"
set capture_PduList(icmptimestampreply,all) {code checksum transmit identifier receive seqnum type originate}

# IcmpTimestampRequest
set capture_PduList(icmptimestamprequest)                      icmptimestamprequest
set capture_PduList(icmptimestamprequest,stc)                  icmp:IcmpTimestampRequest
set capture_PduList(icmptimestamprequest,code)            "code"
set capture_PduList(icmptimestamprequest,code,verify)      "none"
set capture_PduList(icmptimestamprequest,checksum)        "checksum"
set capture_PduList(icmptimestamprequest,checksum,verify)      "none"
set capture_PduList(icmptimestamprequest,transmit)        "transmit"
set capture_PduList(icmptimestamprequest,transmit,verify)      "none"
set capture_PduList(icmptimestamprequest,identifier)      "identifier"
set capture_PduList(icmptimestamprequest,identifier,verify)      "none"
set capture_PduList(icmptimestamprequest,receive)         "receive"
set capture_PduList(icmptimestamprequest,receive,verify)      "none"
set capture_PduList(icmptimestamprequest,seqnum)          "seqnum"
set capture_PduList(icmptimestamprequest,seqnum,verify)      "none"
set capture_PduList(icmptimestamprequest,type)            "type"
set capture_PduList(icmptimestamprequest,type,verify)      "none"
set capture_PduList(icmptimestamprequest,originate)       "originate"
set capture_PduList(icmptimestamprequest,originate,verify)      "none"
set capture_PduList(icmptimestamprequest,all) {code checksum transmit identifier receive seqnum type originate}

# Icmpv6DestUnreach
set capture_PduList(icmpv6destunreach)                      icmpv6destunreach
set capture_PduList(icmpv6destunreach,stc)                  icmpv6:Icmpv6DestUnreach
set capture_PduList(icmpv6destunreach,checksum)        "checksum"
set capture_PduList(icmpv6destunreach,checksum,verify)      "none"
set capture_PduList(icmpv6destunreach,code)            "code"
set capture_PduList(icmpv6destunreach,code,verify)      "none"
set capture_PduList(icmpv6destunreach,unused)          "unused"
set capture_PduList(icmpv6destunreach,unused,verify)      "none"
set capture_PduList(icmpv6destunreach,type)            "type"
set capture_PduList(icmpv6destunreach,type,verify)      "none"
set capture_PduList(icmpv6destunreach,all) {checksum code unused type}

# Icmpv6EchoReply
set capture_PduList(icmpv6echoreply)                      icmpv6echoreply
set capture_PduList(icmpv6echoreply,stc)                  icmpv6:Icmpv6EchoReply
set capture_PduList(icmpv6echoreply,identifier)      "identifier"
set capture_PduList(icmpv6echoreply,identifier,verify)      "none"
set capture_PduList(icmpv6echoreply,checksum)        "checksum"
set capture_PduList(icmpv6echoreply,checksum,verify)      "none"
set capture_PduList(icmpv6echoreply,code)            "code"
set capture_PduList(icmpv6echoreply,code,verify)      "none"
set capture_PduList(icmpv6echoreply,seqnum)          "seqnum"
set capture_PduList(icmpv6echoreply,seqnum,verify)      "none"
set capture_PduList(icmpv6echoreply,data)            "data"
set capture_PduList(icmpv6echoreply,data,verify)      "none"
set capture_PduList(icmpv6echoreply,type)            "type"
set capture_PduList(icmpv6echoreply,type,verify)      "none"
set capture_PduList(icmpv6echoreply,all) {identifier checksum code seqnum data type}

# Icmpv6EchoRequest
set capture_PduList(icmpv6echorequest)                      icmpv6echorequest
set capture_PduList(icmpv6echorequest,stc)                  icmpv6:Icmpv6EchoRequest
set capture_PduList(icmpv6echorequest,identifier)      "identifier"
set capture_PduList(icmpv6echorequest,identifier,verify)      "none"
set capture_PduList(icmpv6echorequest,checksum)        "checksum"
set capture_PduList(icmpv6echorequest,checksum,verify)      "none"
set capture_PduList(icmpv6echorequest,code)            "code"
set capture_PduList(icmpv6echorequest,code,verify)      "none"
set capture_PduList(icmpv6echorequest,seqnum)          "seqnum"
set capture_PduList(icmpv6echorequest,seqnum,verify)      "none"
set capture_PduList(icmpv6echorequest,data)            "data"
set capture_PduList(icmpv6echorequest,data,verify)      "none"
set capture_PduList(icmpv6echorequest,type)            "type"
set capture_PduList(icmpv6echorequest,type,verify)      "none"
set capture_PduList(icmpv6echorequest,all) {identifier checksum code seqnum data type}

# Icmpv6IpData
set capture_PduList(icmpv6ipdata)                      icmpv6ipdata
set capture_PduList(icmpv6ipdata,stc)                  icmpv6:Icmpv6IpData
set capture_PduList(icmpv6ipdata,data)            "data"
set capture_PduList(icmpv6ipdata,data,verify)      "none"
set capture_PduList(icmpv6ipdata,all) {data}

# Icmpv6PacketTooBig
set capture_PduList(icmpv6packettoobig)                      icmpv6packettoobig
set capture_PduList(icmpv6packettoobig,stc)                  icmpv6:Icmpv6PacketTooBig
set capture_PduList(icmpv6packettoobig,checksum)        "checksum"
set capture_PduList(icmpv6packettoobig,checksum,verify)      "none"
set capture_PduList(icmpv6packettoobig,code)            "code"
set capture_PduList(icmpv6packettoobig,code,verify)      "none"
set capture_PduList(icmpv6packettoobig,mtu)             "mtu"
set capture_PduList(icmpv6packettoobig,mtu,verify)      "none"
set capture_PduList(icmpv6packettoobig,type)            "type"
set capture_PduList(icmpv6packettoobig,type,verify)      "none"
set capture_PduList(icmpv6packettoobig,all) {checksum code mtu type}

# Icmpv6ParameterProblem
set capture_PduList(icmpv6parameterproblem)                      icmpv6parameterproblem
set capture_PduList(icmpv6parameterproblem,stc)                  icmpv6:Icmpv6ParameterProblem
set capture_PduList(icmpv6parameterproblem,checksum)        "checksum"
set capture_PduList(icmpv6parameterproblem,checksum,verify)      "none"
set capture_PduList(icmpv6parameterproblem,code)            "code"
set capture_PduList(icmpv6parameterproblem,code,verify)      "none"
set capture_PduList(icmpv6parameterproblem,pointer)         "pointer"
set capture_PduList(icmpv6parameterproblem,pointer,verify)      "none"
set capture_PduList(icmpv6parameterproblem,type)            "type"
set capture_PduList(icmpv6parameterproblem,type,verify)      "none"
set capture_PduList(icmpv6parameterproblem,all) {checksum code pointer type}

# Icmpv6TimeExceeded
set capture_PduList(icmpv6timeexceeded)                      icmpv6timeexceeded
set capture_PduList(icmpv6timeexceeded,stc)                  icmpv6:Icmpv6TimeExceeded
set capture_PduList(icmpv6timeexceeded,checksum)        "checksum"
set capture_PduList(icmpv6timeexceeded,checksum,verify)      "none"
set capture_PduList(icmpv6timeexceeded,code)            "code"
set capture_PduList(icmpv6timeexceeded,code,verify)      "none"
set capture_PduList(icmpv6timeexceeded,unused)          "unused"
set capture_PduList(icmpv6timeexceeded,unused,verify)      "none"
set capture_PduList(icmpv6timeexceeded,type)            "type"
set capture_PduList(icmpv6timeexceeded,type,verify)      "none"
set capture_PduList(icmpv6timeexceeded,all) {checksum code unused type}

# Igmpv1
set capture_PduList(igmpv1)                      igmpv1
set capture_PduList(igmpv1,stc)                  igmp:Igmpv1
set capture_PduList(igmpv1,groupaddress)    "groupaddress"
set capture_PduList(igmpv1,groupaddress,verify)      "none"
set capture_PduList(igmpv1,checksum)        "checksum"
set capture_PduList(igmpv1,checksum,verify)      "none"
set capture_PduList(igmpv1,unused)          "unused"
set capture_PduList(igmpv1,unused,verify)      "none"
set capture_PduList(igmpv1,type)            "type"
set capture_PduList(igmpv1,type,verify)      "none"
set capture_PduList(igmpv1,version)         "version"
set capture_PduList(igmpv1,version,verify)      "none"
set capture_PduList(igmpv1,all) {groupaddress checksum unused type version}

# Igmpv2
set capture_PduList(igmpv2)                      igmpv2
set capture_PduList(igmpv2,stc)                  igmp:Igmpv2
set capture_PduList(igmpv2,groupaddress)    "groupaddress"
set capture_PduList(igmpv2,groupaddress,verify)      "none"
set capture_PduList(igmpv2,checksum)        "checksum"
set capture_PduList(igmpv2,checksum,verify)      "none"
set capture_PduList(igmpv2,maxresptime)     "maxresptime"
set capture_PduList(igmpv2,maxresptime,verify)      "none"
set capture_PduList(igmpv2,type)            "type"
set capture_PduList(igmpv2,type,verify)      "none"
set capture_PduList(igmpv2,all) {groupaddress checksum maxresptime type}

# Igmpv3Query
set capture_PduList(igmpv3query)                      igmpv3query
set capture_PduList(igmpv3query,stc)                  igmp:Igmpv3Query
set capture_PduList(igmpv3query,checksum)        "checksum"
set capture_PduList(igmpv3query,checksum,verify)      "none"
set capture_PduList(igmpv3query,resv)            "resv"
set capture_PduList(igmpv3query,resv,verify)      "none"
set capture_PduList(igmpv3query,numsource)       "numsource"
set capture_PduList(igmpv3query,numsource,verify)      "none"
set capture_PduList(igmpv3query,groupaddress)    "groupaddress"
set capture_PduList(igmpv3query,groupaddress,verify)      "none"
set capture_PduList(igmpv3query,sflag)           "sflag"
set capture_PduList(igmpv3query,sflag,verify)      "none"
set capture_PduList(igmpv3query,qqic)            "qqic"
set capture_PduList(igmpv3query,qqic,verify)      "none"
set capture_PduList(igmpv3query,maxresptime)     "maxresptime"
set capture_PduList(igmpv3query,maxresptime,verify)      "none"
set capture_PduList(igmpv3query,qrv)             "qrv"
set capture_PduList(igmpv3query,qrv,verify)      "none"
set capture_PduList(igmpv3query,type)            "type"
set capture_PduList(igmpv3query,type,verify)      "none"
set capture_PduList(igmpv3query,all) {checksum resv numsource groupaddress sflag qqic maxresptime qrv type}

# Igmpv3Report
set capture_PduList(igmpv3report)                      igmpv3report
set capture_PduList(igmpv3report,stc)                  igmp:Igmpv3Report
set capture_PduList(igmpv3report,numgrprecords)   "numgrprecords"
set capture_PduList(igmpv3report,numgrprecords,verify)      "none"
set capture_PduList(igmpv3report,checksum)        "checksum"
set capture_PduList(igmpv3report,checksum,verify)      "none"
set capture_PduList(igmpv3report,reserved)        "reserved"
set capture_PduList(igmpv3report,reserved,verify)      "none"
set capture_PduList(igmpv3report,reserved2)       "reserved2"
set capture_PduList(igmpv3report,reserved2,verify)      "none"
set capture_PduList(igmpv3report,type)            "type"
set capture_PduList(igmpv3report,type,verify)      "none"
set capture_PduList(igmpv3report,all) {numgrprecords checksum reserved reserved2 type}

# IP
set capture_PduList(ip)                         ip
set capture_PduList(ip,stc)                     ip:IP
set capture_PduList(ip,v6llprefixlength)        "v6llprefixlength"
set capture_PduList(ip,v6llprefixlength,verify)      "none"
set capture_PduList(ip,v6sourceaddr)        "v6sourceaddr"
set capture_PduList(ip,v6sourceaddr,verify)      "none"
set capture_PduList(ip,v6trafficclass)      "v6trafficclass"
set capture_PduList(ip,v6trafficclass,verify)      "none"
set capture_PduList(ip,v6llhoplimit)        "v6llhoplimit"
set capture_PduList(ip,v6llhoplimit,verify)      "none"
set capture_PduList(ip,ttl)                 "ttl"
set capture_PduList(ip,ttl,verify)      "none"
set capture_PduList(ip,sourceaddr)          "sourceaddr"
set capture_PduList(ip,sourceaddr,verify)      "none"
set capture_PduList(ip,v6prefixlength)      "v6prefixlength"
set capture_PduList(ip,v6prefixlength,verify)      "none"
set capture_PduList(ip,v6gateway)           "v6gateway"
set capture_PduList(ip,v6gateway,verify)      "none"
set capture_PduList(ip,v6llsourceaddr)      "v6llsourceaddr"
set capture_PduList(ip,v6llsourceaddr,verify)      "none"
set capture_PduList(ip,prefixlength)        "prefixlength"
set capture_PduList(ip,prefixlength,verify)      "none"
set capture_PduList(ip,v6lltrafficclass)    "v6lltrafficclass"
set capture_PduList(ip,v6lltrafficclass,verify)      "none"
set capture_PduList(ip,gateway)             "gateway"
set capture_PduList(ip,gateway,verify)      "none"
set capture_PduList(ip,v6hoplimit)          "v6hoplimit"
set capture_PduList(ip,v6hoplimit,verify)      "none"
set capture_PduList(ip,all) {v6llprefixlength v6sourceaddr v6trafficclass v6llhoplimit ttl sourceaddr v6prefixlength v6gateway v6llsourceaddr prefixlength v6lltrafficclass gateway v6hoplimit}

# IPv4
set capture_PduList(ipv4)                          ipv4
set capture_PduList(ipv4,stc)                      ipv4:IPv4
set capture_PduList(ipv4,checksum)                 "checksum"
set capture_PduList(ipv4,checksum,verify)          "none"
set capture_PduList(ipv4,ihl)                      "ihl"
set capture_PduList(ipv4,ihl,verify)               "none"
set capture_PduList(ipv4,version)                  "version"
set capture_PduList(ipv4,version,verify)           "int"
set capture_PduList(ipv4,destprefixlength)         "destprefixlength"
set capture_PduList(ipv4,destprefixlength,verify)  "none"
set capture_PduList(ipv4,identification)           "identification"
set capture_PduList(ipv4,identification,verify)    "int"
set capture_PduList(ipv4,protocol)                 "protocol"
set capture_PduList(ipv4,protocol,verify)          "int"
set capture_PduList(ipv4,destaddr)                 "destaddr"
set capture_PduList(ipv4,destaddr,verify)          "ip"
set capture_PduList(ipv4,ttl)                      "ttl"
set capture_PduList(ipv4,ttl,verify)               "int"
set capture_PduList(ipv4,sourceaddr)               "sourceaddr"
set capture_PduList(ipv4,sourceaddr,verify)        "ip"
set capture_PduList(ipv4,totallength)              "totallength"
set capture_PduList(ipv4,totallength,verify)       "int"
set capture_PduList(ipv4,fragoffset)               "fragoffset"
set capture_PduList(ipv4,fragoffset,verify)        "int"
set capture_PduList(ipv4,prefixlength)             "prefixlength"
set capture_PduList(ipv4,prefixlength,verify)      "none"
set capture_PduList(ipv4,gateway)                  "gateway"
set capture_PduList(ipv4,gateway,verify)           "none"
set capture_PduList(ipv4,all) {checksum ihl version destprefixlength identification protocol destaddr ttl sourceaddr totallength fragoffset prefixlength gateway}

# Ipv4Addr
set capture_PduList(ipv4addr)                      ipv4addr
set capture_PduList(ipv4addr,stc)                  ipv4:Ipv4Addr
set capture_PduList(ipv4addr,value)           "value"
set capture_PduList(ipv4addr,value,verify)      "none"
set capture_PduList(ipv4addr,all) {value}

# Ipv4AddressList
set capture_PduList(ipv4addresslist)                      ipv4addresslist
set capture_PduList(ipv4addresslist,stc)                  ipv4:Ipv4AddressList
set capture_PduList(ipv4addresslist,all) {}

# IPv4HeaderOption
set capture_PduList(ipv4headeroption)                      ipv4headeroption
set capture_PduList(ipv4headeroption,stc)                  ipv4:IPv4HeaderOption
set capture_PduList(ipv4headeroption,all) {}

# IPv4HeaderOptionsList
set capture_PduList(ipv4headeroptionslist)                      ipv4headeroptionslist
set capture_PduList(ipv4headeroptionslist,stc)                  ipv4:IPv4HeaderOptionsList
set capture_PduList(ipv4headeroptionslist,all) {}

# Ipv4OptionAddressExtension
set capture_PduList(ipv4optionaddressextension)                      ipv4optionaddressextension
set capture_PduList(ipv4optionaddressextension,stc)                  ipv4:Ipv4OptionAddressExtension
set capture_PduList(ipv4optionaddressextension,dest7thbyte)     "dest7thbyte"
set capture_PduList(ipv4optionaddressextension,dest7thbyte,verify)      "none"
set capture_PduList(ipv4optionaddressextension,sourceipv7)      "sourceipv7"
set capture_PduList(ipv4optionaddressextension,sourceipv7,verify)      "none"
set capture_PduList(ipv4optionaddressextension,source7thbyte)   "source7thbyte"
set capture_PduList(ipv4optionaddressextension,source7thbyte,verify)      "none"
set capture_PduList(ipv4optionaddressextension,destipv7)        "destipv7"
set capture_PduList(ipv4optionaddressextension,destipv7,verify)      "none"
set capture_PduList(ipv4optionaddressextension,length)          "length"
set capture_PduList(ipv4optionaddressextension,length,verify)      "none"
set capture_PduList(ipv4optionaddressextension,type)            "type"
set capture_PduList(ipv4optionaddressextension,type,verify)      "none"
set capture_PduList(ipv4optionaddressextension,all) {dest7thbyte sourceipv7 source7thbyte destipv7 length type}

# Ipv4OptionEndOfOptions
set capture_PduList(ipv4optionendofoptions)                      ipv4optionendofoptions
set capture_PduList(ipv4optionendofoptions,stc)                  ipv4:Ipv4OptionEndOfOptions
set capture_PduList(ipv4optionendofoptions,type)            "type"
set capture_PduList(ipv4optionendofoptions,type,verify)      "none"
set capture_PduList(ipv4optionendofoptions,all) {type}

# Ipv4OptionExtendedSecurity
set capture_PduList(ipv4optionextendedsecurity)                      ipv4optionextendedsecurity
set capture_PduList(ipv4optionextendedsecurity,stc)                  ipv4:Ipv4OptionExtendedSecurity
set capture_PduList(ipv4optionextendedsecurity,addsecinfo)      "addsecinfo"
set capture_PduList(ipv4optionextendedsecurity,addsecinfo,verify)      "none"
set capture_PduList(ipv4optionextendedsecurity,formatcode)      "formatcode"
set capture_PduList(ipv4optionextendedsecurity,formatcode,verify)      "none"
set capture_PduList(ipv4optionextendedsecurity,length)          "length"
set capture_PduList(ipv4optionextendedsecurity,length,verify)      "none"
set capture_PduList(ipv4optionextendedsecurity,type)            "type"
set capture_PduList(ipv4optionextendedsecurity,type,verify)      "none"
set capture_PduList(ipv4optionextendedsecurity,all) {addsecinfo formatcode length type}

# Ipv4OptionLooseSourceRoute
set capture_PduList(ipv4optionloosesourceroute)                      ipv4optionloosesourceroute
set capture_PduList(ipv4optionloosesourceroute,stc)                  ipv4:Ipv4OptionLooseSourceRoute
set capture_PduList(ipv4optionloosesourceroute,pointer)         "pointer"
set capture_PduList(ipv4optionloosesourceroute,pointer,verify)      "none"
set capture_PduList(ipv4optionloosesourceroute,length)          "length"
set capture_PduList(ipv4optionloosesourceroute,length,verify)      "none"
set capture_PduList(ipv4optionloosesourceroute,type)            "type"
set capture_PduList(ipv4optionloosesourceroute,type,verify)      "none"
set capture_PduList(ipv4optionloosesourceroute,all) {pointer length type}

# Ipv4OptionMtuProbe
set capture_PduList(ipv4optionmtuprobe)                      ipv4optionmtuprobe
set capture_PduList(ipv4optionmtuprobe,stc)                  ipv4:Ipv4OptionMtuProbe
set capture_PduList(ipv4optionmtuprobe,mtu)             "mtu"
set capture_PduList(ipv4optionmtuprobe,mtu,verify)      "none"
set capture_PduList(ipv4optionmtuprobe,length)          "length"
set capture_PduList(ipv4optionmtuprobe,length,verify)      "none"
set capture_PduList(ipv4optionmtuprobe,type)            "type"
set capture_PduList(ipv4optionmtuprobe,type,verify)      "none"
set capture_PduList(ipv4optionmtuprobe,all) {mtu length type}

# Ipv4OptionMtuReply
set capture_PduList(ipv4optionmtureply)                      ipv4optionmtureply
set capture_PduList(ipv4optionmtureply,stc)                  ipv4:Ipv4OptionMtuReply
set capture_PduList(ipv4optionmtureply,mtu)             "mtu"
set capture_PduList(ipv4optionmtureply,mtu,verify)      "none"
set capture_PduList(ipv4optionmtureply,length)          "length"
set capture_PduList(ipv4optionmtureply,length,verify)      "none"
set capture_PduList(ipv4optionmtureply,type)            "type"
set capture_PduList(ipv4optionmtureply,type,verify)      "none"
set capture_PduList(ipv4optionmtureply,all) {mtu length type}

# Ipv4OptionNop
set capture_PduList(ipv4optionnop)                      ipv4optionnop
set capture_PduList(ipv4optionnop,stc)                  ipv4:Ipv4OptionNop
set capture_PduList(ipv4optionnop,type)            "type"
set capture_PduList(ipv4optionnop,type,verify)      "none"
set capture_PduList(ipv4optionnop,all) {type}

# Ipv4OptionRecordRoute
set capture_PduList(ipv4optionrecordroute)                      ipv4optionrecordroute
set capture_PduList(ipv4optionrecordroute,stc)                  ipv4:Ipv4OptionRecordRoute
set capture_PduList(ipv4optionrecordroute,pointer)         "pointer"
set capture_PduList(ipv4optionrecordroute,pointer,verify)      "none"
set capture_PduList(ipv4optionrecordroute,length)          "length"
set capture_PduList(ipv4optionrecordroute,length,verify)      "none"
set capture_PduList(ipv4optionrecordroute,type)            "type"
set capture_PduList(ipv4optionrecordroute,type,verify)      "none"
set capture_PduList(ipv4optionrecordroute,all) {pointer length type}

# Ipv4OptionRouterAlert
set capture_PduList(ipv4optionrouteralert)                      ipv4optionrouteralert
set capture_PduList(ipv4optionrouteralert,stc)                  ipv4:Ipv4OptionRouterAlert
set capture_PduList(ipv4optionrouteralert,routeralert)     "routeralert"
set capture_PduList(ipv4optionrouteralert,routeralert,verify)      "none"
set capture_PduList(ipv4optionrouteralert,length)          "length"
set capture_PduList(ipv4optionrouteralert,length,verify)      "none"
set capture_PduList(ipv4optionrouteralert,type)            "type"
set capture_PduList(ipv4optionrouteralert,type,verify)      "none"
set capture_PduList(ipv4optionrouteralert,all) {routeralert length type}

# Ipv4OptionSecurity
set capture_PduList(ipv4optionsecurity)                      ipv4optionsecurity
set capture_PduList(ipv4optionsecurity,stc)                  ipv4:Ipv4OptionSecurity
set capture_PduList(ipv4optionsecurity,txcontrolcode)           "txcontrolcode"
set capture_PduList(ipv4optionsecurity,txcontrolcode,verify)      "none"
set capture_PduList(ipv4optionsecurity,security)                "security"
set capture_PduList(ipv4optionsecurity,security,verify)      "none"
set capture_PduList(ipv4optionsecurity,compartments)            "compartments"
set capture_PduList(ipv4optionsecurity,compartments,verify)      "none"
set capture_PduList(ipv4optionsecurity,handlingrestrictions)    "handlingrestrictions"
set capture_PduList(ipv4optionsecurity,handlingrestrictions,verify)      "none"
set capture_PduList(ipv4optionsecurity,length)                  "length"
set capture_PduList(ipv4optionsecurity,length,verify)      "none"
set capture_PduList(ipv4optionsecurity,type)                    "type"
set capture_PduList(ipv4optionsecurity,type,verify)      "none"
set capture_PduList(ipv4optionsecurity,all) {txcontrolcode security compartments handlingrestrictions length type}

# Ipv4OptionSelectiveBroadcastMode
set capture_PduList(ipv4optionselectivebroadcastmode)                      ipv4optionselectivebroadcastmode
set capture_PduList(ipv4optionselectivebroadcastmode,stc)                  ipv4:Ipv4OptionSelectiveBroadcastMode
set capture_PduList(ipv4optionselectivebroadcastmode,length)          "length"
set capture_PduList(ipv4optionselectivebroadcastmode,length,verify)      "none"
set capture_PduList(ipv4optionselectivebroadcastmode,type)            "type"
set capture_PduList(ipv4optionselectivebroadcastmode,type,verify)      "none"
set capture_PduList(ipv4optionselectivebroadcastmode,all) {length type}

# Ipv4OptionStreamIdentifier
set capture_PduList(ipv4optionstreamidentifier)                      ipv4optionstreamidentifier
set capture_PduList(ipv4optionstreamidentifier,stc)                  ipv4:Ipv4OptionStreamIdentifier
set capture_PduList(ipv4optionstreamidentifier,streamid)        "streamid"
set capture_PduList(ipv4optionstreamidentifier,streamid,verify)      "none"
set capture_PduList(ipv4optionstreamidentifier,length)          "length"
set capture_PduList(ipv4optionstreamidentifier,length,verify)      "none"
set capture_PduList(ipv4optionstreamidentifier,type)            "type"
set capture_PduList(ipv4optionstreamidentifier,type,verify)      "none"
set capture_PduList(ipv4optionstreamidentifier,all) {streamid length type}

# Ipv4OptionStrictSourceRoute
set capture_PduList(ipv4optionstrictsourceroute)                      ipv4optionstrictsourceroute
set capture_PduList(ipv4optionstrictsourceroute,stc)                  ipv4:Ipv4OptionStrictSourceRoute
set capture_PduList(ipv4optionstrictsourceroute,pointer)         "pointer"
set capture_PduList(ipv4optionstrictsourceroute,pointer,verify)      "none"
set capture_PduList(ipv4optionstrictsourceroute,length)          "length"
set capture_PduList(ipv4optionstrictsourceroute,length,verify)      "none"
set capture_PduList(ipv4optionstrictsourceroute,type)            "type"
set capture_PduList(ipv4optionstrictsourceroute,type,verify)      "none"
set capture_PduList(ipv4optionstrictsourceroute,all) {pointer length type}

# Ipv4OptionTimeStamp
set capture_PduList(ipv4optiontimestamp)                      ipv4optiontimestamp
set capture_PduList(ipv4optiontimestamp,stc)                  ipv4:Ipv4OptionTimeStamp
set capture_PduList(ipv4optiontimestamp,timestamp)       "timestamp"
set capture_PduList(ipv4optiontimestamp,timestamp,verify)      "none"
set capture_PduList(ipv4optiontimestamp,overflow)        "overflow"
set capture_PduList(ipv4optiontimestamp,overflow,verify)      "none"
set capture_PduList(ipv4optiontimestamp,pointer)         "pointer"
set capture_PduList(ipv4optiontimestamp,pointer,verify)      "none"
set capture_PduList(ipv4optiontimestamp,flag)            "flag"
set capture_PduList(ipv4optiontimestamp,flag,verify)      "none"
set capture_PduList(ipv4optiontimestamp,length)          "length"
set capture_PduList(ipv4optiontimestamp,length,verify)      "none"
set capture_PduList(ipv4optiontimestamp,type)            "type"
set capture_PduList(ipv4optiontimestamp,type,verify)      "none"
set capture_PduList(ipv4optiontimestamp,all) {timestamp overflow pointer flag length type}

# Ipv4OptionTraceRoute
set capture_PduList(ipv4optiontraceroute)                      ipv4optiontraceroute
set capture_PduList(ipv4optiontraceroute,stc)                  ipv4:Ipv4OptionTraceRoute
set capture_PduList(ipv4optiontraceroute,originatorip)    "originatorip"
set capture_PduList(ipv4optiontraceroute,originatorip,verify)      "none"
set capture_PduList(ipv4optiontraceroute,returnhopcnt)    "returnhopcnt"
set capture_PduList(ipv4optiontraceroute,returnhopcnt,verify)      "none"
set capture_PduList(ipv4optiontraceroute,outboundhopcnt)  "outboundhopcnt"
set capture_PduList(ipv4optiontraceroute,outboundhopcnt,verify)      "none"
set capture_PduList(ipv4optiontraceroute,idnumber)        "idnumber"
set capture_PduList(ipv4optiontraceroute,idnumber,verify)      "none"
set capture_PduList(ipv4optiontraceroute,length)          "length"
set capture_PduList(ipv4optiontraceroute,length,verify)      "none"
set capture_PduList(ipv4optiontraceroute,type)            "type"
set capture_PduList(ipv4optiontraceroute,type,verify)      "none"
set capture_PduList(ipv4optiontraceroute,all) {originatorip returnhopcnt outboundhopcnt idnumber length type}

# IPv6
set capture_PduList(ipv6)                      ipv6
set capture_PduList(ipv6,stc)                  ipv6:IPv6
set capture_PduList(ipv6,payloadlength)       "payloadlength"
set capture_PduList(ipv6,payloadlength,verify)      "none"
set capture_PduList(ipv6,version)             "version"
set capture_PduList(ipv6,version,verify)      "none"
set capture_PduList(ipv6,hoplimit)            "hoplimit"
set capture_PduList(ipv6,hoplimit,verify)      "none"
set capture_PduList(ipv6,destprefixlength)    "destprefixlength"
set capture_PduList(ipv6,destprefixlength,verify)      "none"
set capture_PduList(ipv6,flowlabel)           "flowlabel"
set capture_PduList(ipv6,flowlabel,verify)      "none"
set capture_PduList(ipv6,nextheader)          "nextheader"
set capture_PduList(ipv6,nextheader,verify)      "none"
set capture_PduList(ipv6,destaddr)            "destaddr"
set capture_PduList(ipv6,destaddr,verify)      "none"
set capture_PduList(ipv6,sourceaddr)          "sourceaddr"
set capture_PduList(ipv6,sourceaddr,verify)      "none"
set capture_PduList(ipv6,trafficclass)        "trafficclass"
set capture_PduList(ipv6,trafficclass,verify)      "none"
set capture_PduList(ipv6,prefixlength)        "prefixlength"
set capture_PduList(ipv6,prefixlength,verify)      "none"
set capture_PduList(ipv6,gateway)             "gateway"
set capture_PduList(ipv6,gateway,verify)      "none"
set capture_PduList(ipv6,all) {payloadlength version hoplimit destprefixlength flowlabel nextheader destaddr sourceaddr trafficclass prefixlength gateway}

# Ipv6Addr
set capture_PduList(ipv6addr)                      ipv6addr
set capture_PduList(ipv6addr,stc)                  ipv6:Ipv6Addr
set capture_PduList(ipv6addr,value)           "value"
set capture_PduList(ipv6addr,value,verify)      "none"
set capture_PduList(ipv6addr,all) {value}

# Ipv6AuthenticationHeader
set capture_PduList(ipv6authenticationheader)                      ipv6authenticationheader
set capture_PduList(ipv6authenticationheader,stc)                  ipv6:Ipv6AuthenticationHeader
set capture_PduList(ipv6authenticationheader,authdata)        "authdata"
set capture_PduList(ipv6authenticationheader,authdata,verify)      "none"
set capture_PduList(ipv6authenticationheader,spi)             "spi"
set capture_PduList(ipv6authenticationheader,spi,verify)      "none"
set capture_PduList(ipv6authenticationheader,reserved)        "reserved"
set capture_PduList(ipv6authenticationheader,reserved,verify)      "none"
set capture_PduList(ipv6authenticationheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6authenticationheader,nxthdr,verify)      "none"
set capture_PduList(ipv6authenticationheader,seqnum)          "seqnum"
set capture_PduList(ipv6authenticationheader,seqnum,verify)      "none"
set capture_PduList(ipv6authenticationheader,length)          "length"
set capture_PduList(ipv6authenticationheader,length,verify)      "none"
set capture_PduList(ipv6authenticationheader,all) {authdata spi reserved nxthdr seqnum length}

# Ipv6CustomOption
set capture_PduList(ipv6customoption)                      ipv6customoption
set capture_PduList(ipv6customoption,stc)                  ipv6:Ipv6CustomOption
set capture_PduList(ipv6customoption,data)            "data"
set capture_PduList(ipv6customoption,data,verify)      "none"
set capture_PduList(ipv6customoption,type)            "type"
set capture_PduList(ipv6customoption,type,verify)      "none"
set capture_PduList(ipv6customoption,all) {data type}

# Ipv6DestinationHeader
set capture_PduList(ipv6destinationheader)                      ipv6destinationheader
set capture_PduList(ipv6destinationheader,stc)                  ipv6:Ipv6DestinationHeader
set capture_PduList(ipv6destinationheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6destinationheader,nxthdr,verify)      "none"
set capture_PduList(ipv6destinationheader,length)          "length"
set capture_PduList(ipv6destinationheader,length,verify)      "none"
set capture_PduList(ipv6destinationheader,all) {nxthdr length}

# Ipv6DestinationOption
set capture_PduList(ipv6destinationoption)                      ipv6destinationoption
set capture_PduList(ipv6destinationoption,stc)                  ipv6:Ipv6DestinationOption
set capture_PduList(ipv6destinationoption,all) {}

# Ipv6DestinationOptionsList
set capture_PduList(ipv6destinationoptionslist)                      ipv6destinationoptionslist
set capture_PduList(ipv6destinationoptionslist,stc)                  ipv6:Ipv6DestinationOptionsList
set capture_PduList(ipv6destinationoptionslist,all) {}

# Ipv6EncapsulationHeader
set capture_PduList(ipv6encapsulationheader)                      ipv6encapsulationheader
set capture_PduList(ipv6encapsulationheader,stc)                  ipv6:Ipv6EncapsulationHeader
set capture_PduList(ipv6encapsulationheader,paddata)         "paddata"
set capture_PduList(ipv6encapsulationheader,paddata,verify)      "none"
set capture_PduList(ipv6encapsulationheader,authdata)        "authdata"
set capture_PduList(ipv6encapsulationheader,authdata,verify)      "none"
set capture_PduList(ipv6encapsulationheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6encapsulationheader,nxthdr,verify)      "none"
set capture_PduList(ipv6encapsulationheader,payloaddata)     "payloaddata"
set capture_PduList(ipv6encapsulationheader,payloaddata,verify)      "none"
set capture_PduList(ipv6encapsulationheader,spi)             "spi"
set capture_PduList(ipv6encapsulationheader,spi,verify)      "none"
set capture_PduList(ipv6encapsulationheader,seqnum)          "seqnum"
set capture_PduList(ipv6encapsulationheader,seqnum,verify)      "none"
set capture_PduList(ipv6encapsulationheader,length)          "length"
set capture_PduList(ipv6encapsulationheader,length,verify)      "none"
set capture_PduList(ipv6encapsulationheader,all) {paddata authdata nxthdr payloaddata spi seqnum length}

# Ipv6FragmentHeader
set capture_PduList(ipv6fragmentheader)                      ipv6fragmentheader
set capture_PduList(ipv6fragmentheader,stc)                  ipv6:Ipv6FragmentHeader
set capture_PduList(ipv6fragmentheader,fragoffset)      "fragoffset"
set capture_PduList(ipv6fragmentheader,fragoffset,verify)      "none"
set capture_PduList(ipv6fragmentheader,ident)           "ident"
set capture_PduList(ipv6fragmentheader,ident,verify)      "none"
set capture_PduList(ipv6fragmentheader,reserved)        "reserved"
set capture_PduList(ipv6fragmentheader,reserved,verify)      "none"
set capture_PduList(ipv6fragmentheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6fragmentheader,nxthdr,verify)      "none"
set capture_PduList(ipv6fragmentheader,m_flag)          "m_flag"
set capture_PduList(ipv6fragmentheader,m_flag,verify)      "none"
set capture_PduList(ipv6fragmentheader,length)          "length"
set capture_PduList(ipv6fragmentheader,length,verify)      "none"
set capture_PduList(ipv6fragmentheader,all) {fragoffset ident reserved nxthdr m_flag length}

# Ipv6HopByHopHeader
set capture_PduList(ipv6hopbyhopheader)                      ipv6hopbyhopheader
set capture_PduList(ipv6hopbyhopheader,stc)                  ipv6:Ipv6HopByHopHeader
set capture_PduList(ipv6hopbyhopheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6hopbyhopheader,nxthdr,verify)      "none"
set capture_PduList(ipv6hopbyhopheader,length)          "length"
set capture_PduList(ipv6hopbyhopheader,length,verify)      "none"
set capture_PduList(ipv6hopbyhopheader,all) {nxthdr length}

# Ipv6HopByHopOption
set capture_PduList(ipv6hopbyhopoption)                      ipv6hopbyhopoption
set capture_PduList(ipv6hopbyhopoption,stc)                  ipv6:Ipv6HopByHopOption
set capture_PduList(ipv6hopbyhopoption,all) {}

# Ipv6HopByHopOptionsList
set capture_PduList(ipv6hopbyhopoptionslist)                      ipv6hopbyhopoptionslist
set capture_PduList(ipv6hopbyhopoptionslist,stc)                  ipv6:Ipv6HopByHopOptionsList
set capture_PduList(ipv6hopbyhopoptionslist,all) {}

# Ipv6JumboPayloadOption
set capture_PduList(ipv6jumbopayloadoption)                      ipv6jumbopayloadoption
set capture_PduList(ipv6jumbopayloadoption,stc)                  ipv6:Ipv6JumboPayloadOption
set capture_PduList(ipv6jumbopayloadoption,data)            "data"
set capture_PduList(ipv6jumbopayloadoption,data,verify)      "none"
set capture_PduList(ipv6jumbopayloadoption,length)          "length"
set capture_PduList(ipv6jumbopayloadoption,length,verify)      "none"
set capture_PduList(ipv6jumbopayloadoption,type)            "type"
set capture_PduList(ipv6jumbopayloadoption,type,verify)      "none"
set capture_PduList(ipv6jumbopayloadoption,all) {data length type}

# Ipv6Pad1Option
set capture_PduList(ipv6pad1option)                      ipv6pad1option
set capture_PduList(ipv6pad1option,stc)                  ipv6:Ipv6Pad1Option
set capture_PduList(ipv6pad1option,pad1)            "pad1"
set capture_PduList(ipv6pad1option,pad1,verify)      "none"
set capture_PduList(ipv6pad1option,all) {pad1}

# Ipv6PadNOption
set capture_PduList(ipv6padnoption)                      ipv6padnoption
set capture_PduList(ipv6padnoption,stc)                  ipv6:Ipv6PadNOption
set capture_PduList(ipv6padnoption,padding)         "padding"
set capture_PduList(ipv6padnoption,padding,verify)      "none"
set capture_PduList(ipv6padnoption,padn)            "padn"
set capture_PduList(ipv6padnoption,padn,verify)      "none"
set capture_PduList(ipv6padnoption,length)          "length"
set capture_PduList(ipv6padnoption,length,verify)      "none"
set capture_PduList(ipv6padnoption,all) {padding padn length}

# Ipv6RouterAlertOption
set capture_PduList(ipv6routeralertoption)                      ipv6routeralertoption
set capture_PduList(ipv6routeralertoption,stc)                  ipv6:Ipv6RouterAlertOption
set capture_PduList(ipv6routeralertoption,value)           "value"
set capture_PduList(ipv6routeralertoption,value,verify)      "none"
set capture_PduList(ipv6routeralertoption,routeralert)     "routeralert"
set capture_PduList(ipv6routeralertoption,routeralert,verify)      "none"
set capture_PduList(ipv6routeralertoption,length)          "length"
set capture_PduList(ipv6routeralertoption,length,verify)      "none"
set capture_PduList(ipv6routeralertoption,all) {value routeralert length}

# Ipv6RoutingHeader
set capture_PduList(ipv6routingheader)                      ipv6routingheader
set capture_PduList(ipv6routingheader,stc)                  ipv6:Ipv6RoutingHeader
set capture_PduList(ipv6routingheader,reserved)        "reserved"
set capture_PduList(ipv6routingheader,reserved,verify)      "none"
set capture_PduList(ipv6routingheader,nxthdr)          "nxthdr"
set capture_PduList(ipv6routingheader,nxthdr,verify)      "none"
set capture_PduList(ipv6routingheader,segleft)         "segleft"
set capture_PduList(ipv6routingheader,segleft,verify)      "none"
set capture_PduList(ipv6routingheader,routingtype)     "routingtype"
set capture_PduList(ipv6routingheader,routingtype,verify)      "none"
set capture_PduList(ipv6routingheader,length)          "length"
set capture_PduList(ipv6routingheader,length,verify)      "none"
set capture_PduList(ipv6routingheader,all) {reserved nxthdr segleft routingtype length}

# Ipv6SrcList
set capture_PduList(ipv6SrcList)                      ipv6SrcList
set capture_PduList(ipv6SrcList,stc)                  icmpv6:Ipv6SrcList
set capture_PduList(ipv6SrcList,all) {}

# JoinPrunev4GroupRecord
set capture_PduList(joinprunev4grouprecord)                      joinprunev4grouprecord
set capture_PduList(joinprunev4grouprecord,stc)                  pim:JoinPrunev4GroupRecord
set capture_PduList(joinprunev4grouprecord,numjoin)         "numjoin"
set capture_PduList(joinprunev4grouprecord,numjoin,verify)      "none"
set capture_PduList(joinprunev4grouprecord,numprune)        "numprune"
set capture_PduList(joinprunev4grouprecord,numprune,verify)      "none"
set capture_PduList(joinprunev4grouprecord,all) {numjoin numprune}

# JoinPrunev4GroupRecords
set capture_PduList(joinprunev4grouprecords)                      joinprunev4grouprecords
set capture_PduList(joinprunev4grouprecords,stc)                  pim:JoinPrunev4GroupRecords
set capture_PduList(joinprunev4grouprecords,all) {}

# JoinPrunev6GroupRecord
set capture_PduList(joinprunev6grouprecord)                      joinprunev6grouprecord
set capture_PduList(joinprunev6grouprecord,stc)                  pim:JoinPrunev6GroupRecord
set capture_PduList(joinprunev6grouprecord,numjoin)         "numjoin"
set capture_PduList(joinprunev6grouprecord,numjoin,verify)      "none"
set capture_PduList(joinprunev6grouprecord,numprune)        "numprune"
set capture_PduList(joinprunev6grouprecord,numprune,verify)      "none"
set capture_PduList(joinprunev6grouprecord,all) {numjoin numprune}

# JoinPrunev6GroupRecords
set capture_PduList(joinprunev6grouprecords)                      joinprunev6grouprecords
set capture_PduList(joinprunev6grouprecords,stc)                  pim:JoinPrunev6GroupRecords
set capture_PduList(joinprunev6grouprecords,all) {}

# LACP
set capture_PduList(lacp)                      lacp
set capture_PduList(lacp,stc)                  lacp:LACP
set capture_PduList(lacp,partnerportpriority)       "partnerportpriority"
set capture_PduList(lacp,partnerportpriority,verify)      "none"
set capture_PduList(lacp,actorsystemid)             "actorsystemid"
set capture_PduList(lacp,actorsystemid,verify)      "none"
set capture_PduList(lacp,collectormaxdelay)         "collectormaxdelay"
set capture_PduList(lacp,collectormaxdelay,verify)      "none"
set capture_PduList(lacp,partnerreserved)           "partnerreserved"
set capture_PduList(lacp,partnerreserved,verify)      "none"
set capture_PduList(lacp,collectorinformation)      "collectorinformation"
set capture_PduList(lacp,collectorinformation,verify)      "none"
set capture_PduList(lacp,partnersystemid)           "partnersystemid"
set capture_PduList(lacp,partnersystemid,verify)      "none"
set capture_PduList(lacp,version)                   "version"
set capture_PduList(lacp,version,verify)      "none"
set capture_PduList(lacp,actorport)                 "actorport"
set capture_PduList(lacp,actorport,verify)      "none"
set capture_PduList(lacp,collectorreserved)         "collectorreserved"
set capture_PduList(lacp,collectorreserved,verify)      "none"
set capture_PduList(lacp,collectorinformationlength)  "collectorinformationlength"
set capture_PduList(lacp,collectorinformationlength,verify)      "none"
set capture_PduList(lacp,actorsystempriority)       "actorsystempriority"
set capture_PduList(lacp,actorsystempriority,verify)      "none"
set capture_PduList(lacp,partnerport)               "partnerport"
set capture_PduList(lacp,partnerport,verify)      "none"
set capture_PduList(lacp,partnerinformation)        "partnerinformation"
set capture_PduList(lacp,partnerinformation,verify)      "none"
set capture_PduList(lacp,terminatorinformation)     "terminatorinformation"
set capture_PduList(lacp,terminatorinformation,verify)      "none"
set capture_PduList(lacp,partnersystempriority)     "partnersystempriority"
set capture_PduList(lacp,partnersystempriority,verify)      "none"
set capture_PduList(lacp,partnerinformationlength)  "partnerinformationlength"
set capture_PduList(lacp,partnerinformationlength,verify)      "none"
set capture_PduList(lacp,subtype)                   "subtype"
set capture_PduList(lacp,subtype,verify)      "none"
set capture_PduList(lacp,terminatorreserved)        "terminatorreserved"
set capture_PduList(lacp,terminatorreserved,verify)      "none"
set capture_PduList(lacp,terminatorinformationlength)  "terminatorinformationlength"
set capture_PduList(lacp,terminatorinformationlength,verify)      "none"
set capture_PduList(lacp,partnerstate)              "partnerstate"
set capture_PduList(lacp,partnerstate,verify)      "none"
set capture_PduList(lacp,partnerkey)                "partnerkey"
set capture_PduList(lacp,partnerkey,verify)      "none"
set capture_PduList(lacp,actorinformation)          "actorinformation"
set capture_PduList(lacp,actorinformation,verify)      "none"
set capture_PduList(lacp,actorportpriority)         "actorportpriority"
set capture_PduList(lacp,actorportpriority,verify)      "none"
set capture_PduList(lacp,actorreserved)             "actorreserved"
set capture_PduList(lacp,actorreserved,verify)      "none"
set capture_PduList(lacp,actorinformationlength)    "actorinformationlength"
set capture_PduList(lacp,actorinformationlength,verify)      "none"
set capture_PduList(lacp,actorstate)                "actorstate"
set capture_PduList(lacp,actorstate,verify)      "none"
set capture_PduList(lacp,actorkey)                  "actorkey"
set capture_PduList(lacp,actorkey,verify)      "none"
set capture_PduList(lacp,all) {partnerportpriority actorsystemid collectormaxdelay partnerreserved collectorinformation partnersystemid version actorport collectorreserved collectorinformationlength actorsystempriority partnerport partnerinformation terminatorinformation partnersystempriority partnerinformationlength subtype terminatorreserved terminatorinformationlength partnerstate partnerkey actorinformation actorportpriority actorreserved actorinformationlength actorstate actorkey}

# MLDv1
set capture_PduList(mldv1)                      mldv1
set capture_PduList(mldv1,stc)                  icmpv6:MLDv1
set capture_PduList(mldv1,mcastaddr)       "mcastaddr"
set capture_PduList(mldv1,mcastaddr,verify)      "none"
set capture_PduList(mldv1,maxrespdelay)    "maxrespdelay"
set capture_PduList(mldv1,maxrespdelay,verify)      "none"
set capture_PduList(mldv1,checksum)        "checksum"
set capture_PduList(mldv1,checksum,verify)      "none"
set capture_PduList(mldv1,code)            "code"
set capture_PduList(mldv1,code,verify)      "none"
set capture_PduList(mldv1,reserved)        "reserved"
set capture_PduList(mldv1,reserved,verify)      "none"
set capture_PduList(mldv1,type)            "type"
set capture_PduList(mldv1,type,verify)      "none"
set capture_PduList(mldv1,all) {mcastaddr maxrespdelay checksum code reserved type}

# MLDv2GroupRecord
set capture_PduList(mldv2grouprecord)                      mldv2grouprecord
set capture_PduList(mldv2grouprecord,stc)                  icmpv6:MLDv2GroupRecord
set capture_PduList(mldv2grouprecord,mcastaddr)       "mcastaddr"
set capture_PduList(mldv2grouprecord,mcastaddr,verify)      "none"
set capture_PduList(mldv2grouprecord,auxdatalen)      "auxdatalen"
set capture_PduList(mldv2grouprecord,auxdatalen,verify)      "none"
set capture_PduList(mldv2grouprecord,numsource)       "numsource"
set capture_PduList(mldv2grouprecord,numsource,verify)      "none"
set capture_PduList(mldv2grouprecord,recordtype)      "recordtype"
set capture_PduList(mldv2grouprecord,recordtype,verify)      "none"
set capture_PduList(mldv2grouprecord,all) {mcastaddr auxdatalen numsource recordtype}

# MLDv2GroupRecordList
set capture_PduList(mldv2grouprecordlist)                      mldv2grouprecordlist
set capture_PduList(mldv2grouprecordlist,stc)                  icmpv6:MLDv2GroupRecordList
set capture_PduList(mldv2grouprecordlist,all) {}

# MLDv2Query
set capture_PduList(mldv2query)                      mldv2query
set capture_PduList(mldv2query,stc)                  icmpv6:MLDv2Query
set capture_PduList(mldv2query,code)            "code"
set capture_PduList(mldv2query,code,verify)      "none"
set capture_PduList(mldv2query,checksum)        "checksum"
set capture_PduList(mldv2query,checksum,verify)      "none"
set capture_PduList(mldv2query,resv)            "resv"
set capture_PduList(mldv2query,resv,verify)      "none"
set capture_PduList(mldv2query,numsource)       "numsource"
set capture_PduList(mldv2query,numsource,verify)      "none"
set capture_PduList(mldv2query,maxrespcode)     "maxrespcode"
set capture_PduList(mldv2query,maxrespcode,verify)      "none"
set capture_PduList(mldv2query,groupaddress)    "groupaddress"
set capture_PduList(mldv2query,groupaddress,verify)      "none"
set capture_PduList(mldv2query,sflag)           "sflag"
set capture_PduList(mldv2query,sflag,verify)      "none"
set capture_PduList(mldv2query,qqic)            "qqic"
set capture_PduList(mldv2query,qqic,verify)      "none"
set capture_PduList(mldv2query,reserved)        "reserved"
set capture_PduList(mldv2query,reserved,verify)      "none"
set capture_PduList(mldv2query,qrv)             "qrv"
set capture_PduList(mldv2query,qrv,verify)      "none"
set capture_PduList(mldv2query,type)            "type"
set capture_PduList(mldv2query,type,verify)      "none"
set capture_PduList(mldv2query,all) {code checksum resv numsource maxrespcode groupaddress sflag qqic reserved qrv type}

# MLDv2Report
set capture_PduList(mldv2report)                      mldv2report
set capture_PduList(mldv2report,stc)                  icmpv6:MLDv2Report
set capture_PduList(mldv2report,numgrprecords)   "numgrprecords"
set capture_PduList(mldv2report,numgrprecords,verify)      "none"
set capture_PduList(mldv2report,checksum)        "checksum"
set capture_PduList(mldv2report,checksum,verify)      "none"
set capture_PduList(mldv2report,unused)          "unused"
set capture_PduList(mldv2report,unused,verify)      "none"
set capture_PduList(mldv2report,reserved2)       "reserved2"
set capture_PduList(mldv2report,reserved2,verify)      "none"
set capture_PduList(mldv2report,type)            "type"
set capture_PduList(mldv2report,type,verify)      "none"
set capture_PduList(mldv2report,all) {numgrprecords checksum unused reserved2 type}

# Mpls
set capture_PduList(mpls)                      mpls
set capture_PduList(mpls,stc)                  mpls:Mpls
set capture_PduList(mpls,dstmac)          "dstmac"
set capture_PduList(mpls,dstmac,verify)      "none"
set capture_PduList(mpls,ttl)             "ttl"
set capture_PduList(mpls,ttl,verify)      "none"
set capture_PduList(mpls,label)           "label"
set capture_PduList(mpls,label,verify)      "none"
set capture_PduList(mpls,cos)             "cos"
set capture_PduList(mpls,cos,verify)      "none"
set capture_PduList(mpls,sbit)            "sbit"
set capture_PduList(mpls,sbit,verify)      "none"
set capture_PduList(mpls,all) {dstmac ttl label cos sbit}

# MTU
set capture_PduList(mtu)                      mtu
set capture_PduList(mtu,stc)                  icmpv6:MTU
set capture_PduList(mtu,reserved)        "reserved"
set capture_PduList(mtu,reserved,verify)      "none"
set capture_PduList(mtu,mtu)             "mtu"
set capture_PduList(mtu,mtu,verify)      "none"
set capture_PduList(mtu,length)          "length"
set capture_PduList(mtu,length,verify)      "none"
set capture_PduList(mtu,type)            "type"
set capture_PduList(mtu,type,verify)      "none"
set capture_PduList(mtu,all) {reserved mtu length type}

# MTUOption
set capture_PduList(mtuoption)                      mtuoption
set capture_PduList(mtuoption,stc)                  icmpv6:MTUOption
set capture_PduList(mtuoption,all) {}

# NeighborAdvertisement
set capture_PduList(neighboradvertisement)                      neighboradvertisement
set capture_PduList(neighboradvertisement,stc)                  icmpv6:NeighborAdvertisement
set capture_PduList(neighboradvertisement,code)            "code"
set capture_PduList(neighboradvertisement,code,verify)      "none"
set capture_PduList(neighboradvertisement,checksum)        "checksum"
set capture_PduList(neighboradvertisement,checksum,verify)      "none"
set capture_PduList(neighboradvertisement,oflag)           "oflag"
set capture_PduList(neighboradvertisement,oflag,verify)      "none"
set capture_PduList(neighboradvertisement,rflag)           "rflag"
set capture_PduList(neighboradvertisement,rflag,verify)      "none"
set capture_PduList(neighboradvertisement,sflag)           "sflag"
set capture_PduList(neighboradvertisement,sflag,verify)      "none"
set capture_PduList(neighboradvertisement,targetaddress)   "targetaddress"
set capture_PduList(neighboradvertisement,targetaddress,verify)      "none"
set capture_PduList(neighboradvertisement,reserved)        "reserved"
set capture_PduList(neighboradvertisement,reserved,verify)      "none"
set capture_PduList(neighboradvertisement,type)            "type"
set capture_PduList(neighboradvertisement,type,verify)      "none"
set capture_PduList(neighboradvertisement,all) {code checksum oflag rflag sflag targetaddress reserved type}

# NeighborSolicitation
set capture_PduList(neighborsolicitation)                      neighborsolicitation
set capture_PduList(neighborsolicitation,stc)                  icmpv6:NeighborSolicitation
set capture_PduList(neighborsolicitation,checksum)        "checksum"
set capture_PduList(neighborsolicitation,checksum,verify)      "none"
set capture_PduList(neighborsolicitation,code)            "code"
set capture_PduList(neighborsolicitation,code,verify)      "none"
set capture_PduList(neighborsolicitation,reserved)        "reserved"
set capture_PduList(neighborsolicitation,reserved,verify)      "none"
set capture_PduList(neighborsolicitation,targetaddress)   "targetaddress"
set capture_PduList(neighborsolicitation,targetaddress,verify)      "none"
set capture_PduList(neighborsolicitation,type)            "type"
set capture_PduList(neighborsolicitation,type,verify)      "none"
set capture_PduList(neighborsolicitation,all) {checksum code reserved targetaddress type}

# NodeList
set capture_PduList(nodelist)                      nodelist
set capture_PduList(nodelist,stc)                  ipv6:NodeList
set capture_PduList(nodelist,all) {}

# Ospfv2AsExternalLsa
set capture_PduList(ospfv2asexternallsa)                      ospfv2asexternallsa
set capture_PduList(ospfv2asexternallsa,stc)                  ospfv2:Ospfv2AsExternalLsa
set capture_PduList(ospfv2asexternallsa,forwardingaddress)      "forwardingaddress"
set capture_PduList(ospfv2asexternallsa,forwardingaddress,verify)      "none"
set capture_PduList(ospfv2asexternallsa,externalroutetag)       "externalroutetag"
set capture_PduList(ospfv2asexternallsa,externalroutetag,verify)      "none"
set capture_PduList(ospfv2asexternallsa,externalroutemetric)    "externalroutemetric"
set capture_PduList(ospfv2asexternallsa,externalroutemetric,verify)      "none"
set capture_PduList(ospfv2asexternallsa,networkmask)            "networkmask"
set capture_PduList(ospfv2asexternallsa,networkmask,verify)      "none"
set capture_PduList(ospfv2asexternallsa,all) {forwardingaddress externalroutetag externalroutemetric networkmask}

# Ospfv2AttachedRouter
set capture_PduList(ospfv2attachedrouter)                      ospfv2attachedrouter
set capture_PduList(ospfv2attachedrouter,stc)                  ospfv2:Ospfv2AttachedRouter
set capture_PduList(ospfv2attachedrouter,routerid)        "routerid"
set capture_PduList(ospfv2attachedrouter,routerid,verify)      "none"
set capture_PduList(ospfv2attachedrouter,all) {routerid}

# Ospfv2AttachedRouterList
set capture_PduList(ospfv2attachedrouterlist)                      ospfv2attachedrouterlist
set capture_PduList(ospfv2attachedrouterlist,stc)                  ospfv2:Ospfv2AttachedRouterList
set capture_PduList(ospfv2attachedrouterlist,all) {}

# Ospfv2DD
set capture_PduList(ospfv2dd)                      ospfv2dd
set capture_PduList(ospfv2dd,stc)                  ospfv2:Ospfv2DD
set capture_PduList(ospfv2dd,IfMtu)    "IfMtu"
set capture_PduList(ospfv2dd,IfMtu,verify)      "none"
set capture_PduList(ospfv2dd,sequencenumber)  "sequencenumber"
set capture_PduList(ospfv2dd,sequencenumber,verify)      "none"
set capture_PduList(ospfv2dd,all) {IfMtu sequencenumber}

# Ospfv2DDOptions
set capture_PduList(ospfv2ddoptions)                      ospfv2ddoptions
set capture_PduList(ospfv2ddoptions,stc)                  ospfv2:Ospfv2DDOptions
set capture_PduList(ospfv2ddoptions,msbit)           "msbit"
set capture_PduList(ospfv2ddoptions,msbit,verify)      "none"
set capture_PduList(ospfv2ddoptions,ibit)            "ibit"
set capture_PduList(ospfv2ddoptions,ibit,verify)      "none"
set capture_PduList(ospfv2ddoptions,reserved3)       "reserved3"
set capture_PduList(ospfv2ddoptions,reserved3,verify)      "none"
set capture_PduList(ospfv2ddoptions,reserved4)       "reserved4"
set capture_PduList(ospfv2ddoptions,reserved4,verify)      "none"
set capture_PduList(ospfv2ddoptions,mbit)            "mbit"
set capture_PduList(ospfv2ddoptions,mbit,verify)      "none"
set capture_PduList(ospfv2ddoptions,reserved5)       "reserved5"
set capture_PduList(ospfv2ddoptions,reserved5,verify)      "none"
set capture_PduList(ospfv2ddoptions,reserved6)       "reserved6"
set capture_PduList(ospfv2ddoptions,reserved6,verify)      "none"
set capture_PduList(ospfv2ddoptions,reserved7)       "reserved7"
set capture_PduList(ospfv2ddoptions,reserved7,verify)      "none"
set capture_PduList(ospfv2ddoptions,all) {msbit ibit reserved3 reserved4 mbit reserved5 reserved6 reserved7}

# Ospfv2ExternalLsaOptions
set capture_PduList(ospfv2externallsaoptions)                      ospfv2externallsaoptions
set capture_PduList(ospfv2externallsaoptions,stc)                  ospfv2:Ospfv2ExternalLsaOptions
set capture_PduList(ospfv2externallsaoptions,reserved)        "reserved"
set capture_PduList(ospfv2externallsaoptions,reserved,verify)      "none"
set capture_PduList(ospfv2externallsaoptions,ebit)            "ebit"
set capture_PduList(ospfv2externallsaoptions,ebit,verify)      "none"
set capture_PduList(ospfv2externallsaoptions,all) {reserved ebit}

# Ospfv2ExternalLsaTosMetric
set capture_PduList(ospfv2externallsatosmetric)                      ospfv2externallsatosmetric
set capture_PduList(ospfv2externallsatosmetric,stc)                  ospfv2:Ospfv2ExternalLsaTosMetric
set capture_PduList(ospfv2externallsatosmetric,externallsaroutetos)        "externallsaroutetos"
set capture_PduList(ospfv2externallsatosmetric,externallsaroutetos,verify)      "none"
set capture_PduList(ospfv2externallsatosmetric,ebit)                       "ebit"
set capture_PduList(ospfv2externallsatosmetric,ebit,verify)      "none"
set capture_PduList(ospfv2externallsatosmetric,forwardingaddress)          "forwardingaddress"
set capture_PduList(ospfv2externallsatosmetric,forwardingaddress,verify)      "none"
set capture_PduList(ospfv2externallsatosmetric,externallsaroutemetrics)    "externallsaroutemetrics"
set capture_PduList(ospfv2externallsatosmetric,externallsaroutemetrics,verify)      "none"
set capture_PduList(ospfv2externallsatosmetric,all) {externallsaroutetos ebit forwardingaddress externallsaroutemetrics}

# Ospfv2ExternalLsaTosMetricList
set capture_PduList(ospfv2externallsatosmetriclist)                      ospfv2externallsatosmetriclist
set capture_PduList(ospfv2externallsatosmetriclist,stc)                  ospfv2:Ospfv2ExternalLsaTosMetricList
set capture_PduList(ospfv2externallsatosmetriclist,all) {}

# Ospfv2Header
set capture_PduList(ospfv2header)                      ospfv2header
set capture_PduList(ospfv2header,stc)                  ospfv2:Ospfv2Header
set capture_PduList(ospfv2header,checksum)        "checksum"
set capture_PduList(ospfv2header,checksum,verify)      "none"
set capture_PduList(ospfv2header,areaid)          "areaid"
set capture_PduList(ospfv2header,areaid,verify)      "none"
set capture_PduList(ospfv2header,routerid)        "routerid"
set capture_PduList(ospfv2header,routerid,verify)      "none"
set capture_PduList(ospfv2header,packetlength)    "packetlength"
set capture_PduList(ospfv2header,packetlength,verify)      "none"
set capture_PduList(ospfv2header,type)            "type"
set capture_PduList(ospfv2header,type,verify)      "none"
set capture_PduList(ospfv2header,version)         "version"
set capture_PduList(ospfv2header,version,verify)      "none"
set capture_PduList(ospfv2header,all) {checksum areaid routerid packetlength type version}

# Ospfv2Hello
set capture_PduList(ospfv2hello)                      ospfv2hello
set capture_PduList(ospfv2hello,stc)                  ospfv2:Ospfv2Hello
set capture_PduList(ospfv2hello,backupdesignatedrouter)  "backupdesignatedrouter"
set capture_PduList(ospfv2hello,backupdesignatedrouter,verify)      "none"
set capture_PduList(ospfv2hello,routerpriority)      "routerpriority"
set capture_PduList(ospfv2hello,routerpriority,verify)      "none"
set capture_PduList(ospfv2hello,routerdeadinterval)  "routerdeadinterval"
set capture_PduList(ospfv2hello,routerdeadinterval,verify)      "none"
set capture_PduList(ospfv2hello,designatedrouter)    "designatedrouter"
set capture_PduList(ospfv2hello,designatedrouter,verify)      "none"
set capture_PduList(ospfv2hello,HelloInterval)       "HelloInterval"
set capture_PduList(ospfv2hello,HelloInterval,verify)      "none"
set capture_PduList(ospfv2hello,networkmask)         "networkmask"
set capture_PduList(ospfv2hello,networkmask,verify)      "none"
set capture_PduList(ospfv2hello,all) {backupdesignatedrouter routerpriority routerdeadinterval designatedrouter HelloInterval networkmask}

# Ospfv2Lsa
set capture_PduList(ospfv2lsa)                      ospfv2lsa
set capture_PduList(ospfv2lsa,stc)                  ospfv2:Ospfv2Lsa
set capture_PduList(ospfv2lsa,all) {}

# Ospfv2LSA
set capture_PduList(ospfv2lsa)                      ospfv2lsa
set capture_PduList(ospfv2lsa,stc)                  ospfv2:Ospfv2LSA
set capture_PduList(ospfv2lsa,all) {}

# Ospfv2LsaHeader
set capture_PduList(ospfv2lsaheader)                      ospfv2lsaheader
set capture_PduList(ospfv2lsaheader,stc)                  ospfv2:Ospfv2LsaHeader
set capture_PduList(ospfv2lsaheader,linkstateid)          "linkstateid"
set capture_PduList(ospfv2lsaheader,linkstateid,verify)      "none"
set capture_PduList(ospfv2lsaheader,lssequencenumber)     "lssequencenumber"
set capture_PduList(ospfv2lsaheader,lssequencenumber,verify)      "none"
set capture_PduList(ospfv2lsaheader,AdvertisingRouterId)    "AdvertisingRouterId"
set capture_PduList(ospfv2lsaheader,AdvertisingRouterId,verify)      "none"
set capture_PduList(ospfv2lsaheader,lstype)               "lstype"
set capture_PduList(ospfv2lsaheader,lstype,verify)      "none"
set capture_PduList(ospfv2lsaheader,lsaage)               "lsaage"
set capture_PduList(ospfv2lsaheader,lsaage,verify)      "none"
set capture_PduList(ospfv2lsaheader,lsalength)            "lsalength"
set capture_PduList(ospfv2lsaheader,lsalength,verify)      "none"
set capture_PduList(ospfv2lsaheader,lschecksum)           "lschecksum"
set capture_PduList(ospfv2lsaheader,lschecksum,verify)      "none"
set capture_PduList(ospfv2lsaheader,all) {linkstateid lssequencenumber AdvertisingRouterId lstype lsaage lsalength lschecksum}

# Ospfv2LsaHeaderList
set capture_PduList(ospfv2lsaheaderlist)                      ospfv2lsaheaderlist
set capture_PduList(ospfv2lsaheaderlist,stc)                  ospfv2:Ospfv2LsaHeaderList
set capture_PduList(ospfv2lsaheaderlist,all) {}

# Ospfv2LSR
set capture_PduList(ospfv2lsr)                      ospfv2lsr
set capture_PduList(ospfv2lsr,stc)                  ospfv2:Ospfv2LSR
set capture_PduList(ospfv2lsr,all) {}

# Ospfv2LSU
set capture_PduList(ospfv2lsu)                      ospfv2lsu
set capture_PduList(ospfv2lsu,stc)                  ospfv2:Ospfv2LSU
set capture_PduList(ospfv2lsu,numberoflsas)    "numberoflsas"
set capture_PduList(ospfv2lsu,numberoflsas,verify)      "none"
set capture_PduList(ospfv2lsu,all) {numberoflsas}

# Ospfv2Neighbor
set capture_PduList(ospfv2neighbor)                      ospfv2neighbor
set capture_PduList(ospfv2neighbor,stc)                  ospfv2:Ospfv2Neighbor
set capture_PduList(ospfv2neighbor,NeighborSystemId)      "NeighborSystemId"
set capture_PduList(ospfv2neighbor,NeighborSystemId,verify)      "none"
set capture_PduList(ospfv2neighbor,all) {NeighborSystemId}

# Ospfv2NeighborList
set capture_PduList(ospfv2neighborlist)                      ospfv2neighborlist
set capture_PduList(ospfv2neighborlist,stc)                  ospfv2:Ospfv2NeighborList
set capture_PduList(ospfv2neighborlist,all) {}

# Ospfv2NetworkLsa
set capture_PduList(ospfv2networklsa)                      ospfv2networklsa
set capture_PduList(ospfv2networklsa,stc)                  ospfv2:Ospfv2NetworkLsa
set capture_PduList(ospfv2networklsa,networkmask)     "networkmask"
set capture_PduList(ospfv2networklsa,networkmask,verify)      "none"
set capture_PduList(ospfv2networklsa,all) {networkmask}

# Ospfv2Options
set capture_PduList(ospfv2options)                      ospfv2options
set capture_PduList(ospfv2options,stc)                  ospfv2:Ospfv2Options
set capture_PduList(ospfv2options,ebit)            "ebit"
set capture_PduList(ospfv2options,ebit,verify)      "none"
set capture_PduList(ospfv2options,mcbit)           "mcbit"
set capture_PduList(ospfv2options,mcbit,verify)      "none"
set capture_PduList(ospfv2options,reserved0)       "reserved0"
set capture_PduList(ospfv2options,reserved0,verify)      "none"
set capture_PduList(ospfv2options,eabit)           "eabit"
set capture_PduList(ospfv2options,eabit,verify)      "none"
set capture_PduList(ospfv2options,npbit)           "npbit"
set capture_PduList(ospfv2options,npbit,verify)      "none"
set capture_PduList(ospfv2options,reserved6)       "reserved6"
set capture_PduList(ospfv2options,reserved6,verify)      "none"
set capture_PduList(ospfv2options,dcbit)           "dcbit"
set capture_PduList(ospfv2options,dcbit,verify)      "none"
set capture_PduList(ospfv2options,reserved7)       "reserved7"
set capture_PduList(ospfv2options,reserved7,verify)      "none"
set capture_PduList(ospfv2options,all) {ebit mcbit reserved0 eabit npbit reserved6 dcbit reserved7}

# Ospfv2RequestedLsa
set capture_PduList(ospfv2requestedlsa)                      ospfv2requestedlsa
set capture_PduList(ospfv2requestedlsa,stc)                  ospfv2:Ospfv2RequestedLsa
set capture_PduList(ospfv2requestedlsa,linkstateid)          "linkstateid"
set capture_PduList(ospfv2requestedlsa,linkstateid,verify)      "none"
set capture_PduList(ospfv2requestedlsa,AdvertisingRouterId)    "AdvertisingRouterId"
set capture_PduList(ospfv2requestedlsa,AdvertisingRouterId,verify)      "none"
set capture_PduList(ospfv2requestedlsa,lstypewide)           "lstypewide"
set capture_PduList(ospfv2requestedlsa,lstypewide,verify)      "none"
set capture_PduList(ospfv2requestedlsa,all) {linkstateid AdvertisingRouterId lstypewide}

# Ospfv2RequestedLsaList
set capture_PduList(ospfv2requestedlsalist)                      ospfv2requestedlsalist
set capture_PduList(ospfv2requestedlsalist,stc)                  ospfv2:Ospfv2RequestedLsaList
set capture_PduList(ospfv2requestedlsalist,all) {}

# Ospfv2RouterLsa
set capture_PduList(ospfv2routerlsa)                      ospfv2routerlsa
set capture_PduList(ospfv2routerlsa,stc)                  ospfv2:Ospfv2RouterLsa
set capture_PduList(ospfv2routerlsa,numberoflinks)         "numberoflinks"
set capture_PduList(ospfv2routerlsa,numberoflinks,verify)      "none"
set capture_PduList(ospfv2routerlsa,routerlsareserved1)    "routerlsareserved1"
set capture_PduList(ospfv2routerlsa,routerlsareserved1,verify)      "none"
set capture_PduList(ospfv2routerlsa,all) {numberoflinks routerlsareserved1}

# Ospfv2RouterLsaLink
set capture_PduList(ospfv2routerlsalink)                      ospfv2routerlsalink
set capture_PduList(ospfv2routerlsalink,stc)                  ospfv2:Ospfv2RouterLsaLink
set capture_PduList(ospfv2routerlsalink,linkid)                    "linkid"
set capture_PduList(ospfv2routerlsalink,linkid,verify)      "none"
set capture_PduList(ospfv2routerlsalink,linkdata)                  "linkdata"
set capture_PduList(ospfv2routerlsalink,linkdata,verify)      "none"
set capture_PduList(ospfv2routerlsalink,routerlsalinktype)         "routerlsalinktype"
set capture_PduList(ospfv2routerlsalink,routerlsalinktype,verify)      "none"
set capture_PduList(ospfv2routerlsalink,routerlinkmetrics)         "routerlinkmetrics"
set capture_PduList(ospfv2routerlsalink,routerlinkmetrics,verify)      "none"
set capture_PduList(ospfv2routerlsalink,numrouterlsatosmetrics)    "numrouterlsatosmetrics"
set capture_PduList(ospfv2routerlsalink,numrouterlsatosmetrics,verify)      "none"
set capture_PduList(ospfv2routerlsalink,all) {linkid linkdata routerlsalinktype routerlinkmetrics numrouterlsatosmetrics}

# Ospfv2RouterLsaLinkList
set capture_PduList(ospfv2routerlsalinklist)                      ospfv2routerlsalinklist
set capture_PduList(ospfv2routerlsalinklist,stc)                  ospfv2:Ospfv2RouterLsaLinkList
set capture_PduList(ospfv2routerlsalinklist,all) {}

# Ospfv2RouterLsaOptions
set capture_PduList(ospfv2routerlsaoptions)                      ospfv2routerlsaoptions
set capture_PduList(ospfv2routerlsaoptions,stc)                  ospfv2:Ospfv2RouterLsaOptions
set capture_PduList(ospfv2routerlsaoptions,ebit)            "ebit"
set capture_PduList(ospfv2routerlsaoptions,ebit,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,bbit)            "bbit"
set capture_PduList(ospfv2routerlsaoptions,bbit,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,reserved3)       "reserved3"
set capture_PduList(ospfv2routerlsaoptions,reserved3,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,reserved4)       "reserved4"
set capture_PduList(ospfv2routerlsaoptions,reserved4,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,reserved5)       "reserved5"
set capture_PduList(ospfv2routerlsaoptions,reserved5,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,vbit)            "vbit"
set capture_PduList(ospfv2routerlsaoptions,vbit,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,reserved6)       "reserved6"
set capture_PduList(ospfv2routerlsaoptions,reserved6,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,reserved7)       "reserved7"
set capture_PduList(ospfv2routerlsaoptions,reserved7,verify)      "none"
set capture_PduList(ospfv2routerlsaoptions,all) {ebit bbit reserved3 reserved4 reserved5 vbit reserved6 reserved7}

# Ospfv2RouterLsaTosMetric
set capture_PduList(ospfv2routerlsatosmetric)                      ospfv2routerlsatosmetric
set capture_PduList(ospfv2routerlsatosmetric,stc)                  ospfv2:Ospfv2RouterLsaTosMetric
set capture_PduList(ospfv2routerlsatosmetric,routertoslinkmetrics)  "routertoslinkmetrics"
set capture_PduList(ospfv2routerlsatosmetric,routertoslinkmetrics,verify)      "none"
set capture_PduList(ospfv2routerlsatosmetric,routerlsametricreserved)  "routerlsametricreserved"
set capture_PduList(ospfv2routerlsatosmetric,routerlsametricreserved,verify)      "none"
set capture_PduList(ospfv2routerlsatosmetric,routerlsalinktype)    "routerlsalinktype"
set capture_PduList(ospfv2routerlsatosmetric,routerlsalinktype,verify)      "none"
set capture_PduList(ospfv2routerlsatosmetric,all) {routertoslinkmetrics routerlsametricreserved routerlsalinktype}

# Ospfv2RouterLsaTosMetricList
set capture_PduList(ospfv2routerlsatosmetriclist)                      ospfv2routerlsatosmetriclist
set capture_PduList(ospfv2routerlsatosmetriclist,stc)                  ospfv2:Ospfv2RouterLsaTosMetricList
set capture_PduList(ospfv2routerlsatosmetriclist,all) {}

# Ospfv2SummaryAsbrLsa
set capture_PduList(ospfv2summaryasbrlsa)                      ospfv2summaryasbrlsa
set capture_PduList(ospfv2summaryasbrlsa,stc)                  ospfv2:Ospfv2SummaryAsbrLsa
set capture_PduList(ospfv2summaryasbrlsa,summarylsareserved1)  "summarylsareserved1"
set capture_PduList(ospfv2summaryasbrlsa,summarylsareserved1,verify)      "none"
set capture_PduList(ospfv2summaryasbrlsa,summarylsametric)    "summarylsametric"
set capture_PduList(ospfv2summaryasbrlsa,summarylsametric,verify)      "none"
set capture_PduList(ospfv2summaryasbrlsa,networkmask)         "networkmask"
set capture_PduList(ospfv2summaryasbrlsa,networkmask,verify)      "none"
set capture_PduList(ospfv2summaryasbrlsa,all) {summarylsareserved1 summarylsametric networkmask}

# Ospfv2SummaryLsa
set capture_PduList(ospfv2summarylsa)                      ospfv2summarylsa
set capture_PduList(ospfv2summarylsa,stc)                  ospfv2:Ospfv2SummaryLsa
set capture_PduList(ospfv2summarylsa,summarylsareserved1)  "summarylsareserved1"
set capture_PduList(ospfv2summarylsa,summarylsareserved1,verify)      "none"
set capture_PduList(ospfv2summarylsa,summarylsametric)    "summarylsametric"
set capture_PduList(ospfv2summarylsa,summarylsametric,verify)      "none"
set capture_PduList(ospfv2summarylsa,networkmask)         "networkmask"
set capture_PduList(ospfv2summarylsa,networkmask,verify)      "none"
set capture_PduList(ospfv2summarylsa,all) {summarylsareserved1 summarylsametric networkmask}

# Ospfv2SummaryLsaTosMetric
set capture_PduList(ospfv2summarylsatosmetric)                      ospfv2summarylsatosmetric
set capture_PduList(ospfv2summarylsatosmetric,stc)                  ospfv2:Ospfv2SummaryLsaTosMetric
set capture_PduList(ospfv2summarylsatosmetric,routertoslinkmetrics)        "routertoslinkmetrics"
set capture_PduList(ospfv2summarylsatosmetric,routertoslinkmetrics,verify)      "none"
set capture_PduList(ospfv2summarylsatosmetric,summarylsametricreserved)    "summarylsametricreserved"
set capture_PduList(ospfv2summarylsatosmetric,summarylsametricreserved,verify)      "none"
set capture_PduList(ospfv2summarylsatosmetric,all) {routertoslinkmetrics summarylsametricreserved}

# Ospfv2SummaryLsaTosMetricList
set capture_PduList(ospfv2summarylsatosmetriclist)                      ospfv2summarylsatosmetriclist
set capture_PduList(ospfv2summarylsatosmetriclist,stc)                  ospfv2:Ospfv2SummaryLsaTosMetricList
set capture_PduList(ospfv2summarylsatosmetriclist,all) {}

# Ospfv2Unknown
set capture_PduList(ospfv2unknown)                      ospfv2unknown
set capture_PduList(ospfv2unknown,stc)                  ospfv2:Ospfv2Unknown
set capture_PduList(ospfv2unknown,all) {}

# Ospfv2UpdatedLsaList
set capture_PduList(ospfv2updatedlsalist)                      ospfv2updatedlsalist
set capture_PduList(ospfv2updatedlsalist,stc)                  ospfv2:Ospfv2UpdatedLsaList
set capture_PduList(ospfv2updatedlsalist,all) {}

# PimHelloDRPriority
set capture_PduList(pimhellodrpriority)                      pimhellodrpriority
set capture_PduList(pimhellodrpriority,stc)                  pim:PimHelloDRPriority
set capture_PduList(pimhellodrpriority,value)           "value"
set capture_PduList(pimhellodrpriority,value,verify)      "none"
set capture_PduList(pimhellodrpriority,length)          "length"
set capture_PduList(pimhellodrpriority,length,verify)      "none"
set capture_PduList(pimhellodrpriority,type)            "type"
set capture_PduList(pimhellodrpriority,type,verify)      "none"
set capture_PduList(pimhellodrpriority,all) {value length type}

# PimHelloGenerationID
set capture_PduList(pimhellogenerationid)                      pimhellogenerationid
set capture_PduList(pimhellogenerationid,stc)                  pim:PimHelloGenerationID
set capture_PduList(pimhellogenerationid,value)           "value"
set capture_PduList(pimhellogenerationid,value,verify)      "none"
set capture_PduList(pimhellogenerationid,length)          "length"
set capture_PduList(pimhellogenerationid,length,verify)      "none"
set capture_PduList(pimhellogenerationid,type)            "type"
set capture_PduList(pimhellogenerationid,type,verify)      "none"
set capture_PduList(pimhellogenerationid,all) {value length type}

# PimHelloHoldTime
set capture_PduList(pimhelloholdtime)                      pimhelloholdtime
set capture_PduList(pimhelloholdtime,stc)                  pim:PimHelloHoldTime
set capture_PduList(pimhelloholdtime,value)           "value"
set capture_PduList(pimhelloholdtime,value,verify)      "none"
set capture_PduList(pimhelloholdtime,length)          "length"
set capture_PduList(pimhelloholdtime,length,verify)      "none"
set capture_PduList(pimhelloholdtime,type)            "type"
set capture_PduList(pimhelloholdtime,type,verify)      "none"
set capture_PduList(pimhelloholdtime,all) {value length type}

# PimHelloLanPruneDelay
set capture_PduList(pimhellolanprunedelay)                      pimhellolanprunedelay
set capture_PduList(pimhellolanprunedelay,stc)                  pim:PimHelloLanPruneDelay
set capture_PduList(pimhellolanprunedelay,tbit)               "tbit"
set capture_PduList(pimhellolanprunedelay,tbit,verify)      "none"
set capture_PduList(pimhellolanprunedelay,overrideintervalvalue)  "overrideintervalvalue"
set capture_PduList(pimhellolanprunedelay,overrideintervalvalue,verify)      "none"
set capture_PduList(pimhellolanprunedelay,prunedelayvalue)    "prunedelayvalue"
set capture_PduList(pimhellolanprunedelay,prunedelayvalue,verify)      "none"
set capture_PduList(pimhellolanprunedelay,length)             "length"
set capture_PduList(pimhellolanprunedelay,length,verify)      "none"
set capture_PduList(pimhellolanprunedelay,type)               "type"
set capture_PduList(pimhellolanprunedelay,type,verify)      "none"
set capture_PduList(pimhellolanprunedelay,all) {tbit overrideintervalvalue prunedelayvalue length type}

# Pimv4Assert
set capture_PduList(pimv4assert)                      pimv4assert
set capture_PduList(pimv4assert,stc)                  pim:Pimv4Assert
set capture_PduList(pimv4assert,metric)          "metric"
set capture_PduList(pimv4assert,metric,verify)      "none"
set capture_PduList(pimv4assert,metricpref)      "metricpref"
set capture_PduList(pimv4assert,metricpref,verify)      "none"
set capture_PduList(pimv4assert,rbit)            "rbit"
set capture_PduList(pimv4assert,rbit,verify)      "none"
set capture_PduList(pimv4assert,all) {metric metricpref rbit}

# Pimv4Header
set capture_PduList(pimv4header)                      pimv4header
set capture_PduList(pimv4header,stc)                  pim:Pimv4Header
set capture_PduList(pimv4header,checksum)        "checksum"
set capture_PduList(pimv4header,checksum,verify)      "none"
set capture_PduList(pimv4header,reserved)        "reserved"
set capture_PduList(pimv4header,reserved,verify)      "none"
set capture_PduList(pimv4header,type)            "type"
set capture_PduList(pimv4header,type,verify)      "none"
set capture_PduList(pimv4header,version)         "version"
set capture_PduList(pimv4header,version,verify)      "none"
set capture_PduList(pimv4header,all) {checksum reserved type version}

# Pimv4Hello
set capture_PduList(pimv4hello)                      pimv4hello
set capture_PduList(pimv4hello,stc)                  pim:Pimv4Hello
set capture_PduList(pimv4hello,all) {}

# Pimv4HelloAddressList
set capture_PduList(pimv4helloaddresslist)                      pimv4helloaddresslist
set capture_PduList(pimv4helloaddresslist,stc)                  pim:Pimv4HelloAddressList
set capture_PduList(pimv4helloaddresslist,length)          "length"
set capture_PduList(pimv4helloaddresslist,length,verify)      "none"
set capture_PduList(pimv4helloaddresslist,type)            "type"
set capture_PduList(pimv4helloaddresslist,type,verify)      "none"
set capture_PduList(pimv4helloaddresslist,all) {length type}

# Pimv4HelloOption
set capture_PduList(pimv4hellooption)                      pimv4hellooption
set capture_PduList(pimv4hellooption,stc)                  pim:Pimv4HelloOption
set capture_PduList(pimv4hellooption,all) {}

# Pimv4HelloOptionsList
set capture_PduList(pimv4hellooptionslist)                      pimv4hellooptionslist
set capture_PduList(pimv4hellooptionslist,stc)                  pim:Pimv4HelloOptionsList
set capture_PduList(pimv4hellooptionslist,all) {}

# Pimv4JoinPrune
set capture_PduList(pimv4joinprune)                      pimv4joinprune
set capture_PduList(pimv4joinprune,stc)                  pim:Pimv4JoinPrune
set capture_PduList(pimv4joinprune,numgroups)       "numgroups"
set capture_PduList(pimv4joinprune,numgroups,verify)      "none"
set capture_PduList(pimv4joinprune,reserved)        "reserved"
set capture_PduList(pimv4joinprune,reserved,verify)      "none"
set capture_PduList(pimv4joinprune,holdtime)        "holdtime"
set capture_PduList(pimv4joinprune,holdtime,verify)      "none"
set capture_PduList(pimv4joinprune,all) {numgroups reserved holdtime}

# Pimv4Register
set capture_PduList(pimv4register)                      pimv4register
set capture_PduList(pimv4register,stc)                  pim:Pimv4Register
set capture_PduList(pimv4register,reserved)           "reserved"
set capture_PduList(pimv4register,reserved,verify)      "none"
set capture_PduList(pimv4register,borderbit)          "borderbit"
set capture_PduList(pimv4register,borderbit,verify)      "none"
set capture_PduList(pimv4register,multicastpacket)    "multicastpacket"
set capture_PduList(pimv4register,multicastpacket,verify)      "none"
set capture_PduList(pimv4register,nullbit)            "nullbit"
set capture_PduList(pimv4register,nullbit,verify)      "none"
set capture_PduList(pimv4register,all) {reserved borderbit multicastpacket nullbit}

# Pimv4RegisterStop
set capture_PduList(pimv4registerstop)                      pimv4registerstop
set capture_PduList(pimv4registerstop,stc)                  pim:Pimv4RegisterStop
set capture_PduList(pimv4registerstop,all) {}

# Pimv4SecondaryAddressList
set capture_PduList(pimv4secondaryaddresslist)                      pimv4secondaryaddresslist
set capture_PduList(pimv4secondaryaddresslist,stc)                  pim:Pimv4SecondaryAddressList
set capture_PduList(pimv4secondaryaddresslist,all) {}

# Pimv6Assert
set capture_PduList(pimv6assert)                      pimv6assert
set capture_PduList(pimv6assert,stc)                  pim:Pimv6Assert
set capture_PduList(pimv6assert,metric)          "metric"
set capture_PduList(pimv6assert,metric,verify)      "none"
set capture_PduList(pimv6assert,metricpref)      "metricpref"
set capture_PduList(pimv6assert,metricpref,verify)      "none"
set capture_PduList(pimv6assert,rbit)            "rbit"
set capture_PduList(pimv6assert,rbit,verify)      "none"
set capture_PduList(pimv6assert,all) {metric metricpref rbit}

# Pimv6Header
set capture_PduList(pimv6header)                      pimv6header
set capture_PduList(pimv6header,stc)                  pim:Pimv6Header
set capture_PduList(pimv6header,checksum)        "checksum"
set capture_PduList(pimv6header,checksum,verify)      "none"
set capture_PduList(pimv6header,reserved)        "reserved"
set capture_PduList(pimv6header,reserved,verify)      "none"
set capture_PduList(pimv6header,type)            "type"
set capture_PduList(pimv6header,type,verify)      "none"
set capture_PduList(pimv6header,version)         "version"
set capture_PduList(pimv6header,version,verify)      "none"
set capture_PduList(pimv6header,all) {checksum reserved type version}

# Pimv6Hello
set capture_PduList(pimv6hello)                      pimv6hello
set capture_PduList(pimv6hello,stc)                  pim:Pimv6Hello
set capture_PduList(pimv6hello,all) {}

# Pimv6HelloAddressList
set capture_PduList(pimv6helloaddresslist)                      pimv6helloaddresslist
set capture_PduList(pimv6helloaddresslist,stc)                  pim:Pimv6HelloAddressList
set capture_PduList(pimv6helloaddresslist,length)          "length"
set capture_PduList(pimv6helloaddresslist,length,verify)      "none"
set capture_PduList(pimv6helloaddresslist,type)            "type"
set capture_PduList(pimv6helloaddresslist,type,verify)      "none"
set capture_PduList(pimv6helloaddresslist,all) {length type}

# Pimv6HelloOption
set capture_PduList(pimv6hellooption)                      pimv6hellooption
set capture_PduList(pimv6hellooption,stc)                  pim:Pimv6HelloOption
set capture_PduList(pimv6hellooption,all) {}

# Pimv6HelloOptionsList
set capture_PduList(pimv6hellooptionslist)                      pimv6hellooptionslist
set capture_PduList(pimv6hellooptionslist,stc)                  pim:Pimv6HelloOptionsList
set capture_PduList(pimv6hellooptionslist,all) {}

# Pimv6JoinPrune
set capture_PduList(pimv6joinprune)                      pimv6joinprune
set capture_PduList(pimv6joinprune,stc)                  pim:Pimv6JoinPrune
set capture_PduList(pimv6joinprune,numgroups)       "numgroups"
set capture_PduList(pimv6joinprune,numgroups,verify)      "none"
set capture_PduList(pimv6joinprune,reserved)        "reserved"
set capture_PduList(pimv6joinprune,reserved,verify)      "none"
set capture_PduList(pimv6joinprune,holdtime)        "holdtime"
set capture_PduList(pimv6joinprune,holdtime,verify)      "none"
set capture_PduList(pimv6joinprune,all) {numgroups reserved holdtime}

# Pimv6Register
set capture_PduList(pimv6register)                      pimv6register
set capture_PduList(pimv6register,stc)                  pim:Pimv6Register
set capture_PduList(pimv6register,reserved)           "reserved"
set capture_PduList(pimv6register,reserved,verify)      "none"
set capture_PduList(pimv6register,borderbit)          "borderbit"
set capture_PduList(pimv6register,borderbit,verify)      "none"
set capture_PduList(pimv6register,multicastpacket)    "multicastpacket"
set capture_PduList(pimv6register,multicastpacket,verify)      "none"
set capture_PduList(pimv6register,nullbit)            "nullbit"
set capture_PduList(pimv6register,nullbit,verify)      "none"
set capture_PduList(pimv6register,all) {reserved borderbit multicastpacket nullbit}

# Pimv6RegisterStop
set capture_PduList(pimv6registerstop)                      pimv6registerstop
set capture_PduList(pimv6registerstop,stc)                  pim:Pimv6RegisterStop
set capture_PduList(pimv6registerstop,all) {}

# Pimv6SecondaryAddressList
set capture_PduList(pimv6secondaryaddresslist)                      pimv6secondaryaddresslist
set capture_PduList(pimv6secondaryaddresslist,stc)                  pim:Pimv6SecondaryAddressList
set capture_PduList(pimv6secondaryaddresslist,all) {}

# POS
set capture_PduList(pos)                      pos
set capture_PduList(pos,stc)                  pos:POS
set capture_PduList(pos,protocoltype)    "protocoltype"
set capture_PduList(pos,protocoltype,verify)      "none"
set capture_PduList(pos,control)         "control"
set capture_PduList(pos,control,verify)      "none"
set capture_PduList(pos,address)         "address"
set capture_PduList(pos,address,verify)      "none"
set capture_PduList(pos,all) {protocoltype control address}

# PPP
set capture_PduList(ppp)                      ppp
set capture_PduList(ppp,stc)                  ppp:PPP
set capture_PduList(ppp,protocoltype)    "protocoltype"
set capture_PduList(ppp,protocoltype,verify)      "none"
set capture_PduList(ppp,all) {protocoltype}

# PPPoEDiscovery
set capture_PduList(pppoediscovery)                      pppoediscovery
set capture_PduList(pppoediscovery,stc)                  pppoe:PPPoEDiscovery
set capture_PduList(pppoediscovery,code)            "code"
set capture_PduList(pppoediscovery,code,verify)      "none"
set capture_PduList(pppoediscovery,sessionid)       "sessionid"
set capture_PduList(pppoediscovery,sessionid,verify)      "none"
set capture_PduList(pppoediscovery,length)          "length"
set capture_PduList(pppoediscovery,length,verify)      "none"
set capture_PduList(pppoediscovery,type)            "type"
set capture_PduList(pppoediscovery,type,verify)      "none"
set capture_PduList(pppoediscovery,version)         "version"
set capture_PduList(pppoediscovery,version,verify)      "none"
set capture_PduList(pppoediscovery,all) {code sessionid length type version}

# PPPoESession
set capture_PduList(pppoesession)                      pppoesession
set capture_PduList(pppoesession,stc)                  pppoe:PPPoESession
set capture_PduList(pppoesession,code)            "code"
set capture_PduList(pppoesession,code,verify)      "none"
set capture_PduList(pppoesession,sessionid)       "sessionid"
set capture_PduList(pppoesession,sessionid,verify)      "none"
set capture_PduList(pppoesession,length)          "length"
set capture_PduList(pppoesession,length,verify)      "none"
set capture_PduList(pppoesession,type)            "type"
set capture_PduList(pppoesession,type,verify)      "none"
set capture_PduList(pppoesession,version)         "version"
set capture_PduList(pppoesession,version,verify)      "none"
set capture_PduList(pppoesession,all) {code sessionid length type version}

# PPPoETag
set capture_PduList(pppoetag)                      pppoetag
set capture_PduList(pppoetag,stc)                  pppoe:PPPoETag
set capture_PduList(pppoetag,all) {}

# PPPoETagsList
set capture_PduList(pppoetagslist)                      pppoetagslist
set capture_PduList(pppoetagslist,stc)                  pppoe:PPPoETagsList
set capture_PduList(pppoetagslist,all) {}

# PrefixInfoOption
set capture_PduList(prefixinfooption)                      prefixinfooption
set capture_PduList(prefixinfooption,stc)                  icmpv6:PrefixInfoOption
set capture_PduList(prefixinfooption,all) {}

# PrefixInformation
set capture_PduList(prefixinformation)                      prefixinformation
set capture_PduList(prefixinformation,stc)                  icmpv6:PrefixInformation
set capture_PduList(prefixinformation,lbit)                 "lbit"
set capture_PduList(prefixinformation,lbit,verify)      "none"
set capture_PduList(prefixinformation,preferredlifetime)    "preferredlifetime"
set capture_PduList(prefixinformation,preferredlifetime,verify)      "none"
set capture_PduList(prefixinformation,reserved1)            "reserved1"
set capture_PduList(prefixinformation,reserved1,verify)      "none"
set capture_PduList(prefixinformation,reserved2)            "reserved2"
set capture_PduList(prefixinformation,reserved2,verify)      "none"
set capture_PduList(prefixinformation,prefixlen)            "prefixlen"
set capture_PduList(prefixinformation,prefixlen,verify)      "none"
set capture_PduList(prefixinformation,prefix)               "prefix"
set capture_PduList(prefixinformation,prefix,verify)      "none"
set capture_PduList(prefixinformation,validlifetime)        "validlifetime"
set capture_PduList(prefixinformation,validlifetime,verify)      "none"
set capture_PduList(prefixinformation,abit)                 "abit"
set capture_PduList(prefixinformation,abit,verify)      "none"
set capture_PduList(prefixinformation,type)                 "type"
set capture_PduList(prefixinformation,type,verify)      "none"
set capture_PduList(prefixinformation,length)               "length"
set capture_PduList(prefixinformation,length,verify)      "none"
set capture_PduList(prefixinformation,all) {lbit preferredlifetime reserved1 reserved2 prefixlen prefix validlifetime abit type length}

# RARP
set capture_PduList(rarp)                      rarp
set capture_PduList(rarp,stc)                  arp:RARP
set capture_PduList(rarp,senderhwaddr)    "senderhwaddr"
set capture_PduList(rarp,senderhwaddr,verify)      "none"
set capture_PduList(rarp,ipaddr)          "ipaddr"
set capture_PduList(rarp,ipaddr,verify)      "none"
set capture_PduList(rarp,senderpaddr)     "senderpaddr"
set capture_PduList(rarp,senderpaddr,verify)      "none"
set capture_PduList(rarp,hardware)        "hardware"
set capture_PduList(rarp,hardware,verify)      "none"
set capture_PduList(rarp,protocol)        "protocol"
set capture_PduList(rarp,protocol,verify)      "none"
set capture_PduList(rarp,ihaddr)          "ihaddr"
set capture_PduList(rarp,ihaddr,verify)      "none"
set capture_PduList(rarp,operation)       "operation"
set capture_PduList(rarp,operation,verify)      "none"
set capture_PduList(rarp,targethwaddr)    "targethwaddr"
set capture_PduList(rarp,targethwaddr,verify)      "none"
set capture_PduList(rarp,targetpaddr)     "targetpaddr"
set capture_PduList(rarp,targetpaddr,verify)      "none"
set capture_PduList(rarp,all) {senderhwaddr ipaddr senderpaddr hardware protocol ihaddr operation targethwaddr targetpaddr}

# Redirect
set capture_PduList(redirect)                      redirect
set capture_PduList(redirect,stc)                  icmpv6:Redirect
set capture_PduList(redirect,checksum)        "checksum"
set capture_PduList(redirect,checksum,verify)      "none"
set capture_PduList(redirect,code)            "code"
set capture_PduList(redirect,code,verify)      "none"
set capture_PduList(redirect,reserved)        "reserved"
set capture_PduList(redirect,reserved,verify)      "none"
set capture_PduList(redirect,targetaddress)   "targetaddress"
set capture_PduList(redirect,targetaddress,verify)      "none"
set capture_PduList(redirect,destaddress)     "destaddress"
set capture_PduList(redirect,destaddress,verify)      "none"
set capture_PduList(redirect,type)            "type"
set capture_PduList(redirect,type,verify)      "none"
set capture_PduList(redirect,all) {checksum code reserved targetaddress destaddress type}

# RedirectedHdrOption
set capture_PduList(redirectedhdroption)                      redirectedhdroption
set capture_PduList(redirectedhdroption,stc)                  icmpv6:RedirectedHdrOption
set capture_PduList(redirectedhdroption,all) {}

# RedirectedHeader
set capture_PduList(redirectedheader)                      redirectedheader
set capture_PduList(redirectedheader,stc)                  icmpv6:RedirectedHeader
set capture_PduList(redirectedheader,reserved1)       "reserved1"
set capture_PduList(redirectedheader,reserved1,verify)      "none"
set capture_PduList(redirectedheader,reserved2)       "reserved2"
set capture_PduList(redirectedheader,reserved2,verify)      "none"
set capture_PduList(redirectedheader,length)          "length"
set capture_PduList(redirectedheader,length,verify)      "none"
set capture_PduList(redirectedheader,type)            "type"
set capture_PduList(redirectedheader,type,verify)      "none"
set capture_PduList(redirectedheader,all) {reserved1 reserved2 length type}

# RelaySessionIdTag
set capture_PduList(relaysessionidtag)                      relaysessionidtag
set capture_PduList(relaysessionidtag,stc)                  pppoe:RelaySessionIdTag
set capture_PduList(relaysessionidtag,value)           "value"
set capture_PduList(relaysessionidtag,value,verify)      "none"
set capture_PduList(relaysessionidtag,length)          "length"
set capture_PduList(relaysessionidtag,length,verify)      "none"
set capture_PduList(relaysessionidtag,type)            "type"
set capture_PduList(relaysessionidtag,type,verify)      "none"
set capture_PduList(relaysessionidtag,all) {value length type}

# Rip1Entry
set capture_PduList(rip1entry)                      rip1entry
set capture_PduList(rip1entry,stc)                  rip:Rip1Entry
set capture_PduList(rip1entry,metric)          "metric"
set capture_PduList(rip1entry,metric,verify)      "none"
set capture_PduList(rip1entry,ipaddr)          "ipaddr"
set capture_PduList(rip1entry,ipaddr,verify)      "none"
set capture_PduList(rip1entry,reserved)        "reserved"
set capture_PduList(rip1entry,reserved,verify)      "none"
set capture_PduList(rip1entry,afi)             "afi"
set capture_PduList(rip1entry,afi,verify)      "none"
set capture_PduList(rip1entry,reserved1)       "reserved1"
set capture_PduList(rip1entry,reserved1,verify)      "none"
set capture_PduList(rip1entry,reserved2)       "reserved2"
set capture_PduList(rip1entry,reserved2,verify)      "none"
set capture_PduList(rip1entry,all) {metric ipaddr reserved afi reserved1 reserved2}

# Rip1EntryList
set capture_PduList(rip1entrylist)                      rip1entrylist
set capture_PduList(rip1entrylist,stc)                  rip:Rip1EntryList
set capture_PduList(rip1entrylist,all) {}

# Rip2Entry
set capture_PduList(rip2entry)                      rip2entry
set capture_PduList(rip2entry,stc)                  rip:Rip2Entry
set capture_PduList(rip2entry,routetag)        "routetag"
set capture_PduList(rip2entry,routetag,verify)      "none"
set capture_PduList(rip2entry,metric)          "metric"
set capture_PduList(rip2entry,metric,verify)      "none"
set capture_PduList(rip2entry,ipaddr)          "ipaddr"
set capture_PduList(rip2entry,ipaddr,verify)      "none"
set capture_PduList(rip2entry,afi)             "afi"
set capture_PduList(rip2entry,afi,verify)      "none"
set capture_PduList(rip2entry,subnetmask)      "subnetmask"
set capture_PduList(rip2entry,subnetmask,verify)      "none"
set capture_PduList(rip2entry,nexthop)         "nexthop"
set capture_PduList(rip2entry,nexthop,verify)      "none"
set capture_PduList(rip2entry,all) {routetag metric ipaddr afi subnetmask nexthop}

# Rip2EntryList
set capture_PduList(rip2entrylist)                      rip2entrylist
set capture_PduList(rip2entrylist,stc)                  rip:Rip2EntryList
set capture_PduList(rip2entrylist,all) {}

# Ripng
set capture_PduList(ripng)                      ripng
set capture_PduList(ripng,stc)                  rip:Ripng
set capture_PduList(ripng,command)         "command"
set capture_PduList(ripng,command,verify)      "none"
set capture_PduList(ripng,reserved)        "reserved"
set capture_PduList(ripng,reserved,verify)      "none"
set capture_PduList(ripng,version)         "version"
set capture_PduList(ripng,version,verify)      "none"
set capture_PduList(ripng,all) {command reserved version}

# RipngEntry
set capture_PduList(ripngentry)                      ripngentry
set capture_PduList(ripngentry,stc)                  rip:RipngEntry
set capture_PduList(ripngentry,routetag)        "routetag"
set capture_PduList(ripngentry,routetag,verify)      "none"
set capture_PduList(ripngentry,metric)          "metric"
set capture_PduList(ripngentry,metric,verify)      "none"
set capture_PduList(ripngentry,ipaddr)          "ipaddr"
set capture_PduList(ripngentry,ipaddr,verify)      "none"
set capture_PduList(ripngentry,prefixlen)       "prefixlen"
set capture_PduList(ripngentry,prefixlen,verify)      "none"
set capture_PduList(ripngentry,all) {routetag metric ipaddr prefixlen}

# RipngEntryList
set capture_PduList(ripngentrylist)                      ripngentrylist
set capture_PduList(ripngentrylist,stc)                  rip:RipngEntryList
set capture_PduList(ripngentrylist,all) {}

# Ripv1
set capture_PduList(ripv1)                      ripv1
set capture_PduList(ripv1,stc)                  rip:Ripv1
set capture_PduList(ripv1,command)         "command"
set capture_PduList(ripv1,command,verify)      "none"
set capture_PduList(ripv1,reserved)        "reserved"
set capture_PduList(ripv1,reserved,verify)      "none"
set capture_PduList(ripv1,version)         "version"
set capture_PduList(ripv1,version,verify)      "none"
set capture_PduList(ripv1,all) {command reserved version}

# Ripv2
set capture_PduList(ripv2)                      ripv2
set capture_PduList(ripv2,stc)                  rip:Ripv2
set capture_PduList(ripv2,command)         "command"
set capture_PduList(ripv2,command,verify)      "none"
set capture_PduList(ripv2,reserved)        "reserved"
set capture_PduList(ripv2,reserved,verify)      "none"
set capture_PduList(ripv2,version)         "version"
set capture_PduList(ripv2,version,verify)      "none"
set capture_PduList(ripv2,all) {command reserved version}

# RouterAdvertisement
set capture_PduList(routeradvertisement)                      routeradvertisement
set capture_PduList(routeradvertisement,stc)                  icmpv6:RouterAdvertisement
set capture_PduList(routeradvertisement,code)            "code"
set capture_PduList(routeradvertisement,code,verify)      "none"
set capture_PduList(routeradvertisement,checksum)        "checksum"
set capture_PduList(routeradvertisement,checksum,verify)      "none"
set capture_PduList(routeradvertisement,retranstime)     "retranstime"
set capture_PduList(routeradvertisement,retranstime,verify)      "none"
set capture_PduList(routeradvertisement,routerlifetime)  "routerlifetime"
set capture_PduList(routeradvertisement,routerlifetime,verify)      "none"
set capture_PduList(routeradvertisement,reserved2)       "reserved2"
set capture_PduList(routeradvertisement,reserved2,verify)      "none"
set capture_PduList(routeradvertisement,mbit)            "mbit"
set capture_PduList(routeradvertisement,mbit,verify)      "none"
set capture_PduList(routeradvertisement,obit)            "obit"
set capture_PduList(routeradvertisement,obit,verify)      "none"
set capture_PduList(routeradvertisement,reachabletime)   "reachabletime"
set capture_PduList(routeradvertisement,reachabletime,verify)      "none"
set capture_PduList(routeradvertisement,curhoplimit)     "curhoplimit"
set capture_PduList(routeradvertisement,curhoplimit,verify)      "none"
set capture_PduList(routeradvertisement,type)            "type"
set capture_PduList(routeradvertisement,type,verify)      "none"
set capture_PduList(routeradvertisement,all) {code checksum retranstime routerlifetime reserved2 mbit obit reachabletime curhoplimit type}

# RouterSolicitation
set capture_PduList(routersolicitation)                      routersolicitation
set capture_PduList(routersolicitation,stc)                  icmpv6:RouterSolicitation
set capture_PduList(routersolicitation,checksum)        "checksum"
set capture_PduList(routersolicitation,checksum,verify)      "none"
set capture_PduList(routersolicitation,code)            "code"
set capture_PduList(routersolicitation,code,verify)      "none"
set capture_PduList(routersolicitation,reserved)        "reserved"
set capture_PduList(routersolicitation,reserved,verify)      "none"
set capture_PduList(routersolicitation,type)            "type"
set capture_PduList(routersolicitation,type,verify)      "none"
set capture_PduList(routersolicitation,all) {checksum code reserved type}

# ServiceNameErrorTag
set capture_PduList(servicenameerrortag)                      servicenameerrortag
set capture_PduList(servicenameerrortag,stc)                  pppoe:ServiceNameErrorTag
set capture_PduList(servicenameerrortag,value)           "value"
set capture_PduList(servicenameerrortag,value,verify)      "none"
set capture_PduList(servicenameerrortag,length)          "length"
set capture_PduList(servicenameerrortag,length,verify)      "none"
set capture_PduList(servicenameerrortag,type)            "type"
set capture_PduList(servicenameerrortag,type,verify)      "none"
set capture_PduList(servicenameerrortag,all) {value length type}

# ServiceNameTag
set capture_PduList(servicenametag)                      servicenametag
set capture_PduList(servicenametag,stc)                  pppoe:ServiceNameTag
set capture_PduList(servicenametag,value)           "value"
set capture_PduList(servicenametag,value,verify)      "none"
set capture_PduList(servicenametag,length)          "length"
set capture_PduList(servicenametag,length,verify)      "none"
set capture_PduList(servicenametag,type)            "type"
set capture_PduList(servicenametag,type,verify)      "none"
set capture_PduList(servicenametag,all) {value length type}

# Snap
set capture_PduList(snap)                      snap
set capture_PduList(snap,stc)                  ethernet:Snap
set capture_PduList(snap,orgcode)         "orgcode"
set capture_PduList(snap,orgcode,verify)      "none"
set capture_PduList(snap,ethernettype)    "ethernettype"
set capture_PduList(snap,ethernettype,verify)      "none"
set capture_PduList(snap,all) {orgcode ethernettype}

# SourceIpv4Addresses
set capture_PduList(sourceipv4addresses)                      sourceipv4addresses
set capture_PduList(sourceipv4addresses,stc)                  pim:SourceIpv4Addresses
set capture_PduList(sourceipv4addresses,all) {}

# SourceIpv6Addresses
set capture_PduList(sourceipv6addresses)                      sourceipv6addresses
set capture_PduList(sourceipv6addresses,stc)                  pim:SourceIpv6Addresses
set capture_PduList(sourceipv6addresses,all) {}

# SrcList
set capture_PduList(SrcList)                      SrcList
set capture_PduList(SrcList,stc)                  igmp:SrcList
set capture_PduList(SrcList,all) {}

# Tcp
set capture_PduList(tcp)                      tcp
set capture_PduList(tcp,stc)                  tcp:Tcp
set capture_PduList(tcp,checksum)        "checksum"
set capture_PduList(tcp,checksum,verify)      "none"
set capture_PduList(tcp,finbit)          "finbit"
set capture_PduList(tcp,finbit,verify)      "none"
set capture_PduList(tcp,ecnbit)          "ecnbit"
set capture_PduList(tcp,ecnbit,verify)      "none"
set capture_PduList(tcp,urgbit)          "urgbit"
set capture_PduList(tcp,urgbit,verify)      "none"
set capture_PduList(tcp,ackbit)          "ackbit"
set capture_PduList(tcp,ackbit,verify)      "none"
set capture_PduList(tcp,acknum)          "acknum"
set capture_PduList(tcp,acknum,verify)      "none"
set capture_PduList(tcp,offset)          "offset"
set capture_PduList(tcp,offset,verify)      "none"
set capture_PduList(tcp,window)          "window"
set capture_PduList(tcp,window,verify)      "none"
set capture_PduList(tcp,synbit)          "synbit"
set capture_PduList(tcp,synbit,verify)      "none"
set capture_PduList(tcp,urgentptr)       "urgentptr"
set capture_PduList(tcp,urgentptr,verify)      "none"
set capture_PduList(tcp,cwrbit)          "cwrbit"
set capture_PduList(tcp,cwrbit,verify)      "none"
set capture_PduList(tcp,destport)        "destport"
set capture_PduList(tcp,destport,verify)      "none"
set capture_PduList(tcp,sourceport)      "sourceport"
set capture_PduList(tcp,sourceport,verify)      "none"
set capture_PduList(tcp,rstbit)          "rstbit"
set capture_PduList(tcp,rstbit,verify)      "none"
set capture_PduList(tcp,reserved)        "reserved"
set capture_PduList(tcp,reserved,verify)      "none"
set capture_PduList(tcp,seqnum)          "seqnum"
set capture_PduList(tcp,seqnum,verify)      "none"
set capture_PduList(tcp,pshbit)          "pshbit"
set capture_PduList(tcp,pshbit,verify)      "none"
set capture_PduList(tcp,all) {checksum finbit ecnbit urgbit ackbit acknum offset window synbit urgentptr cwrbit destport sourceport rstbit reserved seqnum pshbit}

# ToSByte
set capture_PduList(tosbyte)                      tosbyte
set capture_PduList(tosbyte,stc)                  ip:ToSByte
set capture_PduList(tosbyte,tbit)            "tbit"
set capture_PduList(tosbyte,tbit,verify)      "none"
set capture_PduList(tosbyte,dbit)            "dbit"
set capture_PduList(tosbyte,dbit,verify)      "none"
set capture_PduList(tosbyte,reserved)        "reserved"
set capture_PduList(tosbyte,reserved,verify)      "none"
set capture_PduList(tosbyte,rbit)            "rbit"
set capture_PduList(tosbyte,rbit,verify)      "none"
set capture_PduList(tosbyte,precedence)      "precedence"
set capture_PduList(tosbyte,precedence,verify)      "none"
set capture_PduList(tosbyte,all) {tbit dbit reserved rbit precedence}

# ToSDiffServ
set capture_PduList(tosdiffserv)                      tosdiffserv
set capture_PduList(tosdiffserv,stc)                  ip:ToSDiffServ
set capture_PduList(tosdiffserv,all) {}

# Udp
set capture_PduList(udp)                      udp
set capture_PduList(udp,stc)                  udp:Udp
set capture_PduList(udp,checksum)        "checksum"
set capture_PduList(udp,checksum,verify)      "none"
set capture_PduList(udp,destport)        "destport"
set capture_PduList(udp,destport,verify)      "none"
set capture_PduList(udp,length)          "length"
set capture_PduList(udp,length,verify)      "none"
set capture_PduList(udp,sourceport)      "sourceport"
set capture_PduList(udp,sourceport,verify)      "none"
set capture_PduList(udp,all) {checksum destport length sourceport}

# VendorSpecificTag
set capture_PduList(vendorspecifictag)                      vendorspecifictag
set capture_PduList(vendorspecifictag,stc)                  pppoe:VendorSpecificTag
set capture_PduList(vendorspecifictag,value)           "value"
set capture_PduList(vendorspecifictag,value,verify)      "none"
set capture_PduList(vendorspecifictag,length)          "length"
set capture_PduList(vendorspecifictag,length,verify)      "none"
set capture_PduList(vendorspecifictag,type)            "type"
set capture_PduList(vendorspecifictag,type,verify)      "none"
set capture_PduList(vendorspecifictag,all) {value length type}

# Vlan
set capture_PduList(vlan)                      vlan
set capture_PduList(vlan,stc)                  ethernet:Vlan
set capture_PduList(vlan,pri)             "pri"
set capture_PduList(vlan,pri,verify)      "none"
set capture_PduList(vlan,id)              "id"
set capture_PduList(vlan,id,verify)      "none"
set capture_PduList(vlan,cfi)             "cfi"
set capture_PduList(vlan,cfi,verify)      "none"
set capture_PduList(vlan,type)            "type"
set capture_PduList(vlan,type,verify)      "none"
set capture_PduList(vlan,all) {pri id cfi type}

# VlansList
set capture_PduList(vlanslist)                      vlanslist
set capture_PduList(vlanslist,stc)                  ethernet:VlansList
set capture_PduList(vlanslist,all) {}

# All PDUs
set capture_PduList(all) \
                [list \
                   accookietag \
                   acnametag \
                   acsystemerrortag \
                   arp \
                   atm \
                   authselect \
                   ciscohdlc \
                   controlflags \
                   custom \
                   dhcpclientidhwtag \
                   dhcpclientidnonhwtag \
                   dhcpclientmsg \
                   dhcpcustomoptiontag \
                   dhcphostnametag \
                   dhcpleasetimetag \
                   dhcpmessagesizetag \
                   dhcpmessagetag \
                   dhcpmessagetypetag \
                   dhcpoption \
                   dhcpoptionslist \
                   dhcpoptoverloadtag \
                   dhcpreqaddrtag \
                   dhcpreqparamtag \
                   dhcpserveridtag \
                   dhcpservermsg \
                   diffservbyte \
                   encodedgroupipv4address \
                   encodedgroupipv6address \
                   encodedsourceipv4address \
                   encodedsourceipv6address \
                   encodedunicastipv4address \
                   encodedunicastipv6address \
                   endoflisttag \
                   endofoptionstag \
                   ethernet8022 \
                   ethernet8023raw \
                   ethernetii \
                   ethernetsnap \
                   genericerrortag \
                   gre \
                   grechecksum \
                   grechecksumlist \
                   grekey \
                   grekeylist \
                   greseqnum \
                   greseqnumlist \
                   grouprecord \
                   grouprecordlist \
                   hdrauthselectcrypto \
                   hdrauthselectnone \
                   hdrauthselectpassword \
                   hdrauthselectuserdef \
                   hostuniqtag \
                   icmpdestunreach \
                   icmpechoreply \
                   icmpechorequest \
                   icmpinforeply \
                   icmpinforequest \
                   icmpipdata \
                   icmpparameterproblem \
                   icmpredirect \
                   icmpsourcequench \
                   icmptimeexceeded \
                   icmptimestampreply \
                   icmptimestamprequest \
                   icmpv6destunreach \
                   icmpv6echoreply \
                   icmpv6echorequest \
                   icmpv6ipdata \
                   icmpv6packettoobig \
                   icmpv6parameterproblem \
                   icmpv6timeexceeded \
                   igmpv1 \
                   igmpv2 \
                   igmpv3query \
                   igmpv3report \
                   ip \
                   ipv4 \
                   ipv4addr \
                   ipv4addresslist \
                   ipv4headeroption \
                   ipv4headeroptionslist \
                   ipv4optionaddressextension \
                   ipv4optionendofoptions \
                   ipv4optionextendedsecurity \
                   ipv4optionloosesourceroute \
                   ipv4optionmtuprobe \
                   ipv4optionmtureply \
                   ipv4optionnop \
                   ipv4optionrecordroute \
                   ipv4optionrouteralert \
                   ipv4optionsecurity \
                   ipv4optionselectivebroadcastmode \
                   ipv4optionstreamidentifier \
                   ipv4optionstrictsourceroute \
                   ipv4optiontimestamp \
                   ipv4optiontraceroute \
                   ipv6 \
                   ipv6addr \
                   ipv6authenticationheader \
                   ipv6customoption \
                   ipv6destinationheader \
                   ipv6destinationoption \
                   ipv6destinationoptionslist \
                   ipv6encapsulationheader \
                   ipv6fragmentheader \
                   ipv6hopbyhopheader \
                   ipv6hopbyhopoption \
                   ipv6hopbyhopoptionslist \
                   ipv6jumbopayloadoption \
                   ipv6pad1option \
                   ipv6padnoption \
                   ipv6routeralertoption \
                   ipv6routingheader \
                   ipv6SrcList \
                   joinprunev4grouprecord \
                   joinprunev4grouprecords \
                   joinprunev6grouprecord \
                   joinprunev6grouprecords \
                   lacp \
                   mldv1 \
                   mldv2grouprecord \
                   mldv2grouprecordlist \
                   mldv2query \
                   mldv2report \
                   mpls \
                   mtu \
                   mtuoption \
                   neighboradvertisement \
                   neighborsolicitation \
                   nodelist \
                   ospfv2asexternallsa \
                   ospfv2attachedrouter \
                   ospfv2attachedrouterlist \
                   ospfv2dd \
                   ospfv2ddoptions \
                   ospfv2externallsaoptions \
                   ospfv2externallsatosmetric \
                   ospfv2externallsatosmetriclist \
                   ospfv2header \
                   ospfv2hello \
                   ospfv2lsa \
                   ospfv2lsa \
                   ospfv2lsaheader \
                   ospfv2lsaheaderlist \
                   ospfv2lsr \
                   ospfv2lsu \
                   ospfv2neighbor \
                   ospfv2neighborlist \
                   ospfv2networklsa \
                   ospfv2options \
                   ospfv2requestedlsa \
                   ospfv2requestedlsalist \
                   ospfv2routerlsa \
                   ospfv2routerlsalink \
                   ospfv2routerlsalinklist \
                   ospfv2routerlsaoptions \
                   ospfv2routerlsatosmetric \
                   ospfv2routerlsatosmetriclist \
                   ospfv2summaryasbrlsa \
                   ospfv2summarylsa \
                   ospfv2summarylsatosmetric \
                   ospfv2summarylsatosmetriclist \
                   ospfv2unknown \
                   ospfv2updatedlsalist \
                   pimhellodrpriority \
                   pimhellogenerationid \
                   pimhelloholdtime \
                   pimhellolanprunedelay \
                   pimv4assert \
                   pimv4header \
                   pimv4hello \
                   pimv4helloaddresslist \
                   pimv4hellooption \
                   pimv4hellooptionslist \
                   pimv4joinprune \
                   pimv4register \
                   pimv4registerstop \
                   pimv4secondaryaddresslist \
                   pimv6assert \
                   pimv6header \
                   pimv6hello \
                   pimv6helloaddresslist \
                   pimv6hellooption \
                   pimv6hellooptionslist \
                   pimv6joinprune \
                   pimv6register \
                   pimv6registerstop \
                   pimv6secondaryaddresslist \
                   pos \
                   ppp \
                   pppoediscovery \
                   pppoesession \
                   pppoetag \
                   pppoetagslist \
                   prefixinfooption \
                   prefixinformation \
                   rarp \
                   redirect \
                   redirectedhdroption \
                   redirectedheader \
                   relaysessionidtag \
                   rip1entry \
                   rip1entrylist \
                   rip2entry \
                   rip2entrylist \
                   ripng \
                   ripngentry \
                   ripngentrylist \
                   ripv1 \
                   ripv2 \
                   routeradvertisement \
                   routersolicitation \
                   servicenameerrortag \
                   servicenametag \
                   snap \
                   sourceipv4addresses \
                   sourceipv6addresses \
                   SrcList \
                   tcp \
                   tosbyte \
                   tosdiffserv \
                   udp \
                   vendorspecifictag \
                   vlan \
                   vlanslist \
              ]

variable capture_LogicalOps
set capture_LogicalOps(&&)    AND
set capture_LogicalOps(and)   AND
set capture_LogicalOps(||)    OR
set capture_LogicalOps(or)    OR

variable capture_PacketErrorMap
set capture_PacketErrMap(signature)  "SigPresent"
set capture_PacketErrMap(oversize)   "Oversized"
set capture_PacketErrMap(jumbo)      "Jumbo"
set capture_PacketErrMap(undersize)  "Undersized"
set capture_PacketErrMap(invalidfcs) "FcsError"
set capture_PacketErrMap(ipCheckSum)   "Ipv4CheckSumError"
set capture_PacketErrMap(oos)        "SigSeqNumError"
set capture_PacketErrMap(prbs)       "PrbsError"

}



# - STH commands
# packet_config_buffers
# packet_control
# packet_stats
# packet_config_filter
# packet_config_triggers
# packet_info
#
# PacketCapture_GetAllPortList
# PacketCapture_ProcessPort
# PacketCapture_GetCaptureProxyID
# PacketCapture_CaptureStart
# PacketCapture_CaptureStop
# PacketCapture_GetRunState
# PacketCapture_SavePacketsToFile
# PacketCapture_ProcessFiltersTriggers
# PacketCapture_ValidatePatternSequence
# PacketCapture_ValidatePattern
# PacketCapture_ProcessStandardEvents
# PacketCapture_ProcessLength
# PacketCapture_ProcessPatternSequence
# PacketCapture_AddPatternSequence
# PacketCapture_RemovePatternSequence
# PacketCapture_CreateCaptureAnalyzerFilter
#
# - Utilities
# IntToHex
# HexToInt
# IpVerify
# Ipv6Verify
# Ipv6Expand
# MacVerify



###
#  Name:    packet_config_buffers
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Configure the packet capture buffer.  Currently, only "wrap" is supported.
###
proc ::sth::packetCapture::packet_config_buffers {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_config_buffers PacketCapture_configBuffers"
    set cmdState $FAILURE

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 1
    }

    # Action
    set action [string tolower $::sth::packetCapture::packetCapture_userArgs(action)]
    if {(![string match -nocase $action "wrap"]) && (![string match -nocase $action "stop"])} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Invalid value for action: $action.  Should be wrap or stop." {}
        return 1
    }
    ########### Since STC only supports wrap mode, we will have to error on "stop."
    ##########if {[string match -nocase $action "stop"]} {
    ##########    ::sth::sthCore::processError returnKeyedList \
    ##########        "ERROR: Spirent TestCenter does not support \"stop.\" Please use \"wrap.\""
    ##########    return 1
    ##########}
    if {[string match -nocase $action "stop"]} {
        if {[catch {set captureObj [::sth::sthCore::invoke stc::get $portHandle -children-Capture]} getStatus]} {
                set errorMessage "ERROR: Failed to get Capture Object for $portHandle: $getStatus"
                ::sth::sthCore::log error $errorMessage
                set retVal $errorMessage
                return 1
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $captureObj "-BufferMode STOP_ON_FULL"} getStatus]} {
                set errorMessage "ERROR: Failed to Config Capture Object for $portHandle: $getStatus"
                ::sth::sthCore::log error $errorMessage
                set retVal $errorMessage
                return 1
        }
    }
    
    
    
    set cmdState $SUCCESS
    return 0
}


###
#  Name:    packet_control
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Start or stop packet capturing.
###
proc ::sth::packetCapture::packet_control {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_control packetCapture::packet_control"
    set cmdState $FAILURE

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    # Action
    set action [string tolower $::sth::packetCapture::packetCapture_userArgs(action)]
    if {(![string match -nocase $action "start"]) && (![string match -nocase $action "stop"])} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Invalid value for action: $action.  Should be start or stop." {}
        return 0
    }

    # Do the implicit Apply here....
    if {[catch {set retVal [::sth::sthCore::doStcApply]} errMsg]} {
        set errorMessage "ERROR: Failed to $action capture: $errMsg"
        ::sth::sthCore::log error $errorMessage
        ::sth::sthCore::processError returnKeyedList $errorMessage
        return 0
    }

    # Start or stop packet capture
    set cmdStatus ""
    switch -- $action {
        "start" {
            if {[::sth::packetCapture::PacketCapture_CaptureStart $portHandle cmdStatus]} {
                # Error
                ::sth::sthCore::processError returnKeyedList $cmdStatus
                return $returnKeyedList
            }
        }
        "stop" {
            if {[::sth::packetCapture::PacketCapture_CaptureStop $portHandle cmdStatus]} {
                # Error
                ::sth::sthCore::processError returnKeyedList $cmdStatus
                return $returnKeyedList
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList \
                "Invalid value for action $action: $action.  Should be start or stop." {}
            return $returnKeyedList
        }
    }
    set cmdState $SUCCESS
    return 1
}

proc ::sth::packetCapture::add_space {data} {
    set ret ""
    set len [string length $data]
    for {set i 0} {$i < $len} {incr i 2} {
        set j [expr $i + 1]
        set ret [concat $ret [string range $data $i $j]]
    }
    return $ret
}

###
#  Name:    packet_stats
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Save captured packets to file
###
proc ::sth::packetCapture::packet_stats {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_stats packetCapture::packet_stats"
    set cmdState $FAILURE

    # Optional parameters
    set stopCapture 1
    set saveToFile 1
    set format "pcap"
    set filename ""
    set var_num_frames 20
    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    # Action
    set action [string tolower $::sth::packetCapture::packetCapture_userArgs(action)]
    if {(![string match -nocase $action "all"]) && (![string match -nocase $action "filtered"])} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Invalid value for action: $action.  Should be start or stop." {}
        return 0
    }
    # Since STC only supports filtered mode, we will have to error on "all."
    if {[string match -nocase $action "all"]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Spirent TestCenter does not support \"all.\" Please use \"filtered.\""
        return 0
    }
    # Stop (Capture)
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(stop)]} {
        set stopCapture $::sth::packetCapture::packetCapture_userArgs(stop)
    }
    # Save To File (filename and format)
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(format)]} {
        set saveToFile 1
        set format $::sth::packetCapture::packetCapture_userArgs(format)
        if {![string match -nocase $format "pcap"] && ![string match -nocase $format "var"] && ![string match -nocase $format "none"]} {
            ::sth::sthCore::processError returnKeyedList \
                "ERROR: Spirent TestCenter only support \"pcap\" \"var\" and \"none\""
            return 0
        }
        if {[info exists ::sth::packetCapture::packetCapture_userArgs(var_num_frames)]} {
            set var_num_frames $::sth::packetCapture::packetCapture_userArgs(var_num_frames)
        }
        if {[info exists ::sth::packetCapture::packetCapture_userArgs(filename)]} {
            set filename $::sth::packetCapture::packetCapture_userArgs(filename)
        } elseif {[string match -nocase $format "pcap"]} {
            ::sth::sthCore::log warn \
                "Captured packets will be saved to the file \"Spirent_TestCenter-\[timestamp\]-\[port_handle\].pcap."
        }
        # If the user has specified "all" for the port_handle,
        # the port_handle will also be appended on to the filename.
    }

    # Save packets
    if {$saveToFile} {
        foreach porthandle $portHandle {
            set lagName [::sth::sthCore::invoke stc::get $porthandle -portSetMember-sources]
            set runStateRetVal ""
            if {[::sth::packetCapture::PacketCapture_GetRunState $porthandle runStateRetVal]} {
                # Error - could not get running state
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Could not get running state of capture on $portHandle: $runStateRetVal"
                return 0
            } else {
                if {$runStateRetVal} {
                    ::sth::sthCore::log debug \
                        "Capture is runnong on $portHandle and will be stopped so that the packets can be saved to file."
                    set errMsg ""
                    if {[::sth::packetCapture::PacketCapture_CaptureStop $porthandle errMsg]} {
                        ::sth::sthCore::processError returnKeyedList \
                            "ERROR: Failed to stop capture on $portHandle."
                        return 0
                    }
                }
            }
            set errMsg ""
            if {$format eq "pcap"} {
            if {[::sth::packetCapture::PacketCapture_SavePacketsToFile $porthandle errMsg \
                     -filename $filename -format $format]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to save packets to file: $errMsg"
                return 0
            }
            }
			if {$format eq "none"} {
                #for ciena
                set captureid [stc::get $porthandle -children-capture]
                set num_frames [stc::get $captureid -PktCount]
                keylset agg num_frames $num_frames
				keylset portinfo aggregate $agg
                keylset returnKeyedList  $porthandle $portinfo
			}	
            if {$format eq "var"} {
                #get no more than 20 frames info
                set captureid [stc::get $porthandle -children-capture]
                set num_frames [stc::get $captureid -PktCount]
                keylset agg num_frames $num_frames

                if {$num_frames > $var_num_frames} {
                    puts\
                	"Captured packets will only display $var_num_frames packets(totally $num_frames)."
                    set num_frames $var_num_frames
                }
                keylset frame length 0
                keylset frame frame ""
                keylset frames 0 $frame
		    
                for {set frameindex 0} {$frameindex < $num_frames} {incr frameindex} {
                    array set frameinfo [stc::perform CaptureGetFrame -captureproxyid $captureid -frameindex $frameindex]

                    #set length [expr $frameinfo(-DataLength) - $frameinfo(-PreambleLength)]
                    set length $frameinfo(-DataLength)
                    set data $frameinfo(-PacketData)
					set prem_len $frameinfo(-PreambleLength)
					set length [expr $length - $prem_len]
					
					set data [string range $data [expr 2*$prem_len] [string length $data]]
					set data "[::sth::packetCapture::add_space $data]"
			
					keylset frame length $length
                    keylset frame frame $data
                    keylset frames $frameindex $frame
                }

                    set lagHdl [::sth::sthCore::invoke stc::get $porthandle -children-lag]
                    if {[string equal $lagHdl ""] } {
                        keylset portinfo aggregate $agg
                        keylset portinfo frame $frames
                        keylset returnKeyedList  $porthandle $portinfo
                        # fix US35953,[CR22390][P-1] num_frames is always zero for LAG port. But able to get the frames,
                        # num_frames is zero on the GUI .
                        keyldel frame frame 
                        unset frames

                    } else {
                        # fix US35953,[CR22390][P-1] num_frames is always zero for LAG port. But able to get the frames,
                        # if current port is LAG port ,use the first port of portsetmember frame data instead of LGA port frames data.
                        set firstPort [lindex [::sth::sthCore::invoke stc::get $lagHdl -portSetMember-Targets] 0]
                        set protinfo [keylget returnKeyedList $firstPort]
                        keylset returnKeyedList $porthandle $protinfo
                        keyldel frame frame 
                        unset frames
                    }

            }
            
        }
    }
    set errMsg ""
    if {!$stopCapture} {
        # Need to start capture running again.
        if {[::sth::packetCapture::PacketCapture_CaptureStart $portHandle errMsg]} {
            ::sth::sthCore::processError returnKeyedList \
                "ERROR: Failed to restart capture on $portHandle: $errMsg"
            return 0
        }
    }
    set cmdState $SUCCESS
    return 1
}


###
#  Name:    packet_config_filter
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Configure packet capture filters (STC -> "Event")
###
proc ::sth::packetCapture::packet_config_filter {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_config_filter packetCapture::packet_config_filter"
    set cmdState $FAILURE

    # Optional parameters
    set mode "add"
    set filter ""

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    # Mode
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(mode)]} {
        set mode $::sth::packetCapture::packetCapture_userArgs(mode)
    }
    # Filter
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(filter)]} {
        set filter $::sth::packetCapture::packetCapture_userArgs(filter)
    }
    # Process and validate the filters
    array set filterSet ""
    set errMsg ""
    if {[::sth::packetCapture::PacketCapture_ProcessFiltersTriggers $filter "filterSet" $mode "filter" "errMsg"]} {
        ::sth::sthCore::processError returnKeyedList $errMsg
        return 0
    }
    if {![info exists filterSet(type)]} {
        # Done here - there are no filters to add or remove.
        set cmdState $SUCCESS
        return 1
    }
    # Configure the filters in STC
    switch -- $filterSet(type) {
        "standard" {
            set configStdFilt ""
            if {[::sth::packetCapture::PacketCapture_ProcessStandardEvents \
                     $portHandle $filterSet(event) "event" $mode configStdFilt]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to $mode filter $filterSet($filterSet(event)): $configStdFilt"
                return 0
            }
        }
        "length" {
            set configLen ""
            if {[::sth::packetCapture::PacketCapture_ProcessLength \
                     $portHandle $filterSet(length) "event" $mode "configLen"]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to $mode filter length ($filterSet(length)): $configLen"
                return 0
            }
        }
        "pattern" {
            # This option is only available for filters.
            set configPattern ""
            if {[::sth::packetCapture::PacketCapture_ProcessPatternSequence \
                     $portHandle $filterSet(pattern) $mode "configPattern"]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to $mode filter pattern ($filterSet(pattern): $configPattern"
                return 0
            }
        }
        default {
            set errMsg "ERROR: Internal error while trying to add filter of type $filterSet(type)."
            append errMsg "  Expected types are: standard | length | pattern."
            ::sth::sthCore::processError returnKeyedList $errMsg
            return 0
        }
    }
	stc::apply
    set cmdState $SUCCESS
    return 1
}

proc ::sth::packetCapture::convert_hex {hexvalue} {
    set DecList ""
    set hex $hexvalue
    while {[string length $hex] > 2} {
        set length [string length $hex]
        set byte [string range $hex [expr $length - 2] [expr $length - 1]]
        set hex [string range $hex 0 [expr $length - 3]]
        set DecList "[format "%d" "0x$byte"] $DecList"
    }
    set DecList "[format "%d" "0x$hex"] $DecList"
    return $DecList
}

proc ::sth::packetCapture::packet_config_pattern {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_config_pattern packetCapture::packet_config_filter"
    set cmdState $FAILURE

    # Optional parameters
    set mode "add"
    set mask 0
    set offset 0
    set value 0
    set RelationToNextFilter AND
    set FilterDescription ""

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    # Mode
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(mode)]} {
        set mode $::sth::packetCapture::packetCapture_userArgs(mode)
    }
    # mask
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(pattern_mask)]} {
        set mask $::sth::packetCapture::packetCapture_userArgs(pattern_mask)
        set mask [::sth::packetCapture::convert_hex $mask]
    }
    # offset
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(pattern_offset)]} {
        set offset $::sth::packetCapture::packetCapture_userArgs(pattern_offset)
    }
    # value
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(pattern_match)]} {
        set value $::sth::packetCapture::packetCapture_userArgs(pattern_match)
        set value [::sth::packetCapture::convert_hex $value]
    }
    # RelationToNextFilter
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(operator)]} {
        set RelationToNextFilter $::sth::packetCapture::packetCapture_userArgs(operator)
    }
    # FilterDescription
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(pattern_type)]} {
        set FilterDescription $::sth::packetCapture::packetCapture_userArgs(pattern_type)
    }
    set capture [::sth::sthCore::invoke stc::get $portHandle -children-Capture]
    set capturefilter [::sth::sthCore::invoke stc::get $capture -children-CaptureFilter]
    if {"add" eq $mode} {
        set capturealayzerfilter [::sth::sthCore::invoke stc::create CaptureAnalyzerFilter -under $capturefilter]
        ::sth::sthCore::invoke stc::config $capturealayzerfilter -IsSelected true\
            -FilterDescription $FilterDescription\
            -Mask $mask\
            -Offset $offset\
            -RelationToNextFilter $RelationToNextFilter\
            -Value $value\
            -FrameConfig       ""
    } elseif {"reset" eq $mode} {
        set capturealayzerfilters [::sth::sthCore::invoke stc::get $capturefilter -children-CaptureAnalyzerFilter]
        foreach capturealayzerfilter $capturealayzerfilters {
            ::sth::sthCore::invoke stc::delete $capturealayzerfilter
        }
	} elseif {"custom" eq $mode} {
        ::sth::sthCore::invoke stc::config $capture -capturefiltermode "BYTEOFFSETANDRANGE" 
        #CaptureFilter
        set fcs_error $::sth::packetCapture::packetCapture_userArgs(filter_fcserror)
        set pcbs_error $::sth::packetCapture::packetCapture_userArgs(filter_prbserror)
        ::sth::sthCore::invoke stc::config $capturefilter -fcserror $fcs_error -prbserror $pcbs_error
        #CapturePatternExpression
        set capturepatternexpress [::sth::sthCore::invoke stc::create CapturePatternExpression -under $capturefilter]
        set filter_byte $::sth::packetCapture::packetCapture_userArgs(filter_byte)
        set filter_framelength $::sth::packetCapture::packetCapture_userArgs(filter_framelength)
        ::sth::sthCore::invoke stc::config $capturepatternexpress -byteexpression $filter_byte -framelengthexpression $filter_framelength
        
        #CaptureBytePattern       
        set mask_list $::sth::packetCapture::packetCapture_userArgs(byte_mask)
        set offset_list $::sth::packetCapture::packetCapture_userArgs(byte_offset)
        set name_list $::sth::packetCapture::packetCapture_userArgs(byte_name)
        set value_list $::sth::packetCapture::packetCapture_userArgs(byte_value)

        set i 0
        foreach value_item $value_list {
            set name [lindex $name_list $i]
            if {$name != ""} {
                set mask [lindex $mask_list $i]
                if {$mask == ""} {
                    set mask $::sth::packetCapture::packet_config_pattern_default(byte_mask)
                }
                set offset [lindex $offset_list $i]
                if {$offset == ""} {
                    set offset $::sth::packetCapture::packet_config_pattern_default(byte_offset)
                } 
                set capturebytepattern [::sth::sthCore::invoke stc::create CaptureBytePattern -under $capture]
                ::sth::sthCore::invoke stc::config $capturebytepattern -name $name\
                                        -mask $mask\
                                        -offset $offset\
                                        -value $value_item
            }
            incr i
        }
        
        ##CaptureRangePattern
        set min_list $::sth::packetCapture::packetCapture_userArgs(range_min)
        set name_list $::sth::packetCapture::packetCapture_userArgs(range_name)
        set max_list $::sth::packetCapture::packetCapture_userArgs(range_max)

        set i 0
        foreach min $min_list {
            set name [lindex $name_list $i]
            if {$name != ""} {
                set max [lindex $max_list $i]
                if {$max == ""} {
                    set max $::sth::packetCapture::packet_config_pattern_default(range_max)
                } 
                set capturerangepattern [::sth::sthCore::invoke stc::create CaptureRangePattern -under $capture]
                ::sth::sthCore::invoke stc::config $capturerangepattern -name $name -max $max -min $min
            }
            incr i
        }
        
        #CaptureStatisticsFilter
        set statistics_flag $::sth::packetCapture::packetCapture_userArgs(statistics_flag)
        if {$statistics_flag eq 1 || $statistics_flag eq true} {
            set fcserror_list $::sth::packetCapture::packetCapture_userArgs(statistics_fcserror)
            set prbserror_list $::sth::packetCapture::packetCapture_userArgs(statistics_prbserror)
            set byte_list $::sth::packetCapture::packetCapture_userArgs(statistics_byte)
            set framelength_list $::sth::packetCapture::packetCapture_userArgs(statistics_framelength)
            
            set i 0
            foreach fcs $fcserror_list {            
                set prbs [lindex $prbserror_list $i]
                if {$prbs == ""} {
                    set prbs $::sth::packetCapture::packet_config_pattern_default(statistics_prbserror)
                }
                
                set capturestatistics [::sth::sthCore::invoke stc::create CaptureStatisticsFilter -under $capture]
                ::sth::sthCore::invoke stc::config $capturestatistics -fcserror $fcs -prbserror $prbs
                
                set byte [lindex $byte_list $i]
                if {$byte == ""} {
                    set byte $::sth::packetCapture::packet_config_pattern_default(statistics_byte)
                }
                set framelen [lindex $framelength_list $i]
                if {$framelen == ""} {
                    set framelen $::sth::packetCapture::packet_config_pattern_default(statistics_framelength)
                }
                  
                set capturepatternexpress [::sth::sthCore::invoke stc::create CapturePatternExpression -under $capturestatistics]
                ::sth::sthCore::invoke stc::config $capturepatternexpress -byteexpression $byte -framelengthexpression $framelen
                incr i
            }
        }
    }
    set cmdState $SUCCESS
    return $cmdState
}


###
#  Name:    packet_config_triggers
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Configure packet capture triggers (STC -> "StartEvent" and "StopEvent")
###
proc ::sth::packetCapture::packet_config_triggers {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_config_triggers packetCapture::packet_config_triggers"
    set cmdState $FAILURE

    # Optional parameters
    set mode "add"
    set trigger ""

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    # Exec
    set exec $::sth::packetCapture::packetCapture_userArgs(exec)
    # Mode
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(mode)]} {
        set mode $::sth::packetCapture::packetCapture_userArgs(mode)
    }
    # Trigger
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(trigger)]} {
        set trigger $::sth::packetCapture::packetCapture_userArgs(trigger)
    }
    # Action
    if {[info exists ::sth::packetCapture::packetCapture_userArgs(action)]} {
        set action $::sth::packetCapture::packetCapture_userArgs(action)
        # Since STC doesn't support "counter" as an option for action, test for that and throw and error if it is set
        if {[string match -nocase $action "counter"]} {
            ::sth::sthCore::processError returnKeyedList \
                "ERROR: Spirent TestCenter does not support \"counter.\" Please use \"event.\""
            return 0
        }
    }

    # Process and validate the triggers
    array set triggerSet ""
    set errMsg ""
    if {[::sth::packetCapture::PacketCapture_ProcessFiltersTriggers $trigger "triggerSet" $mode "trigger" "errMsg"]} {
        ::sth::sthCore::processError returnKeyedList $errMsg
        return 0
    }
    if {![info exists triggerSet(type)]} {
        # Done here - there are no triggers to add or remove.
        set cmdState $SUCCESS
        return 1
    }
    # Configure the triggers in STC
    switch -- $triggerSet(type) {
        "standard" {
            set configStdTrigger ""
            if {[::sth::packetCapture::PacketCapture_ProcessStandardEvents \
                     $portHandle $triggerSet(event) "[string tolower $exec]event" $mode configStdTrigger]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to $mode trigger $triggerSet($triggerSet(event)): $configStdTrigger"
                return 0
            }
        }
        "length" {
            set configLen ""
            if {[::sth::packetCapture::PacketCapture_ProcessLength \
                     $portHandle $triggerSet(length) "[string tolower $exec]event" $mode "configLen"]} {
                ::sth::sthCore::processError returnKeyedList \
                    "ERROR: Failed to $mode trigger length ($triggerSet(length)): $configLen"
                return 0
            }
        }
        default {
            set errMsg "ERROR: Internal error while trying to add trigger of type $triggerSet(type)."
            append errMsg "  Expected types are: standard | length"
            ::sth::sthCore::processError returnKeyedList $errMsg
            return 0
        }
    }
    set cmdState $SUCCESS
    return 1
}


###
#  Name:    packet_info
#  Inputs:  userInput - user input argument array
#           rklName - returnKeyedList name
#           csName - cmdState name
#  Globals: none.
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Return packet capture information
#  NOTE: "all" not supported as a port handle.
###
proc ::sth::packetCapture::packet_info {userInput rklName csName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 $rklName returnKeyedList
    upvar 1 $csName cmdState

    ::sth::sthCore::log debug "Executing Internal Subcommand for: packet_info packetCapture::packet_info"
    set cmdState $FAILURE

    # Validate the parameters
    # Port
    set portHandle ""
    if {[::sth::packetCapture::PacketCapture_ProcessPort \
             $::sth::packetCapture::packetCapture_userArgs(port_handle) portHandle]} {
        ::sth::sthCore::processError returnKeyedList $portHandle
        return 0
    }
    if {[llength $portHandle] > 1} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: \"all\" not supported for packet_info command -port_handle parameter."
        return 0
    }

    # Action
    set action [string tolower $::sth::packetCapture::packetCapture_userArgs(action)]

    # Get status
    # Usage and Capacity are not supported.
    # Stopped
    set runState ""
    if {[::sth::packetCapture::PacketCapture_GetRunState $portHandle runState]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Could not determine state of capture on $portHandle."
        return 0
    }
    keylset returnKeyedList stopped [expr {!$runState}]
    set cmdState $SUCCESS
    return 1
}



###
#  Name:    PacketCapture_GetAllPortList
#  Inputs:  rvName - return variable name (place to put the return value or the error message)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Collect and return list of all STC port handles
###
proc ::sth::packetCapture::PacketCapture_GetAllPortList {rvName} {
    upvar $rvName retVal
    set retVal ""

    # Using all ports under the project here (assuming only one project)
    if {[catch {set retVal [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Port]} errMsg]} {
        set errorMessage "ERROR: Failed to get ports from under $::sth::GBLHNDMAP(project): $errMsg."
        ::sth::sthCore::log error $errorMessage
        set retVal $errorMessage
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_ProcessPort
#  Inputs:  portHandle - port handle to be validated and expanded if neccessary (if all)
#           rvName - return variable name (will contain either the processed port handles or the error message)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Validate port handle or expand (if all)
###
proc ::sth::packetCapture::PacketCapture_ProcessPort {portHandle rvName} {
    upvar $rvName retVal
    set retVal ""
    if {[string match -nocase $portHandle "all"]} {
        # We are using all of the ports here
        set msg ""
        set cmdStatus ""
        if {[::sth::packetCapture::PacketCapture_GetAllPortList "cmdStatus"]} {
            set retVal "ERROR: Failed to get all port handles: $cmdStatus"
            return 1
        } else {
            set retVal $cmdStatus
        }
    } else {
        if {![::sth::sthCore::IsPortValid $portHandle msg]} {
            set retVal "ERROR: port_handle $portHandle is invalid."
            return 1
        } else {
            set retVal $portHandle
        }
    }
    return 0
}


###
#  Name:    PacketCapture_GetCaptureProxyID
#  Inputs:  portHandleList - STC port handle(s)
#           rvName - name of the return variable (will contain either a list of proxy IDs or an error message)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Collect and return capture proxy IDs from the given port handles
###
proc ::sth::packetCapture::PacketCapture_GetCaptureProxyID {portHandleList rvName} {
    upvar $rvName retVal
    set retVal ""
    foreach portHandle $portHandleList {
        if {[catch {lappend retVal [::sth::sthCore::invoke stc::get $portHandle -children-Capture]} getStatus]} {
            set errorMessage "ERROR: Failed to get Capture ProxyID for $portHandle: $getStatus"
            ::sth::sthCore::log error $errorMessage
            set retVal $errorMessage
            return 1
        }
    }
    return 0
}


###
#  Name:    PacketCapture_CaptureStart
#  Inputs:  portHandleList - STC port handle(s)
#           rvName - name of the return variable (will only contain an error message if necessary here)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Start capture on the given list of port handles
###
proc ::sth::packetCapture::PacketCapture_CaptureStart {portHandleList rvName} {
    upvar $rvName retVal
    set retVal ""
    set proxyIDList ""
    # Get Proxy IDs
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandleList proxyIDList]} {
        set retVal "ERROR: Failed to start capture: $proxyIDList."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    # Start capture on the given ports
    ::sth::sthCore::log debug "Starting capture on $proxyIDList."

    if {[catch {::sth::sthCore::invoke stc::perform "CaptureStart" -captureproxyid $proxyIDList} performStatus]} {
        set retVal "ERROR: Failed to start capture(s) on $portHandleList with error $performStatus."
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_CaptureStop
#  Inputs:  portHandleList - STC port handle(s)
#           rvName - name of the return variable (will only contain an error message if necessary here)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Stop capture on the given list of port handles
###
proc ::sth::packetCapture::PacketCapture_CaptureStop {portHandleList rvName} {
    upvar $rvName retVal
    set retVal ""
    set proxyIDList ""
    # Get Proxy IDs
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandleList proxyIDList]} {
        set retVal "ERROR: Failed to stop capture: $proxyIDList."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    # Stop capture on the given ports
    ::sth::sthCore::log debug "Stopping capture on $proxyIDList."

    if {[catch {::sth::sthCore::invoke stc::perform "CaptureStop" -captureproxyid $proxyIDList} performStatus]} {
        set retVal "ERROR: Failed to stop capture(s) on $portHandleList with error $performStatus."
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_GetRunState
#  Inputs:  portHandle - single STC port handle
#           rvName - name of the return variable - running (1) not running (0)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Determines if capture is running on a port or not
###
proc ::sth::packetCapture::PacketCapture_GetRunState {portHandle rvName} {
    upvar 1 $rvName retVal
    set proxyID ""
    set retVal 0
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandle proxyID]} {
        set retVal "ERROR: Failed to get capture handle from $portHandle."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    if {[catch {::sth::sthCore::invoke stc::get $proxyID -capturestate} runStatus]} {
        set retVal "ERROR: Failed to get status on $portHandle ($proxyID) with error: $runStatus."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    if {[string match -nocase $runStatus "running"]} {
        set retVal 1
    }
    return 0
}


###
#  Name:    PacketCapture_SavePacketsToFile
#  Inputs:  portHandleList - list of STC port handle objects or "all"
#           rvName - name of the return variable (for error messages)
#           args:
#             -filename - filename
#             -format - file format (only pcap is supported currently)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Save the captured packets to a file
#  Note:    Assuming that capture is STOPPED on each of the ports this is being run on.
#           Also note that "filename" does not include the extension - this is added on based on -format.
###
proc ::sth::packetCapture::PacketCapture_SavePacketsToFile {portHandle rvName args} {
    upvar 1 $rvName retVal
    set retVal 0
    array set aArgs $args
    set filename ""
    set useDefaultFilename 1
    set appendPort 0
    set format "pcap"
    if {[info exists aArgs(-filename)] && $aArgs(-filename) != ""} {
        set filename $aArgs(-filename)
        set useDefaultFilename 0
    }
    if {[info exists aArgs(-format)]} {
        set format $aArgs(-format)
    }
    if {[llength $portHandle] > 1} {
        set appendPort 1
    }
    set proxyIDList ""
    set retVal 0
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandle proxyIDList]} {
        set retVal "ERROR: Failed to get capture handle from $portHandle."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    foreach proxyID $proxyIDList {
        # Capture specified packets
        if {$useDefaultFilename} {
            set filename "Spirent_TestCenter-[clock seconds]-$portHandle.$format"
        } else {
            if {[string match -nocase "*.$format" $filename]} {
                # Remove the ".$format" portion -> [string length $format] characters + 1 extra as 
                # first character is actually while string length is as it is.
                # "string trim" (inc. left and right) will keep removing letters until it finds one it
                # can't remove.  Order of the letters to remove DOES NOT MATTER.
                set filename [string range $filename 0 \
                                  [expr {[string length $filename] - (1 + [string length $format])}]]$format
            } else {
                set filename $filename.$format
            }
        }
        ::sth::sthCore::log debug "Saving packets to file $filename on $proxyID."

        if {[catch {::sth::sthCore::invoke stc::perform "CaptureDataSave" -captureproxyid $proxyID -Filename $filename -FilenameFormat $format} performStatus]} {
            set retVal "ERROR: Failed to save capture data on $portHandle ($proxyID) with error $performStatus."
            ::sth::sthCore::log error $retVal
            return 1
        }
        set proxyidParent [::sth::sthCore::invoke stc::get $proxyID -parent]
        set laghdl [::sth::sthCore::invoke stc::get $proxyidParent -children-lag]
        if {[string match -nocase "lag*" $laghdl]} {
            ::sth::sthCore::invoke stc::perform spirent.LagCapture.GetLagCaptureCommand -captureFile [file join [pwd] Untitled $filename] -portSetHandle $proxyidParent
        }

    }
    return 0
}


###
#  Name:    PacketCapture_ProcessFiltersTriggers
#  Inputs:  ftVal - list of filter or trigger info
#           ftiName - name of the filter or trigger array to store parsed information
#           mode - add or remove (to determine if length and parameter need the extra information)
#           eventType - filter | trigger
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Parse and validate the user input filter or triggers
#           Filter or trigger list may contain single word filters (signature, etc.) or
#           Pattern or length.
#  Pattern should be defined as a list of lists that are anded or ored together:
#  {pattern {{-frameconfig ethernetii:ipv4 -pdu ipv4 -field sourceAddr -value 192.1.1.1} AND 
#            {-frameconfig ethernetii:ipv4 -pdu ipv4 -field destAddr -value 192.1.2.1}}}
###
proc ::sth::packetCapture::PacketCapture_ProcessFiltersTriggers {ftVal ftiName mode eventType rvName} {
    variable capture_PacketErrMap
    upvar 1 $ftiName ftInfo
    upvar 1 $rvName retVal
    set retVal ""

    array unset ftInfo
    array set ftInfo ""

    # The length of ftVal should be at most 2.  If any greater, the user has put multiple filters/triggers on the same
    # command which is an error.
    set ltLength [llength $ftVal]
    if {$ltLength == 0} {
        # There are no filters or triggers defined.
        return 0
    } elseif {$ltLength == 1} {
        # Filter or Trigger is a single word.
        switch -- [string tolower $ftVal] {
            signature -
            oversize -
            jumbo -
            undersize -
            invalidfcs -
            ipCheckSum -
            oos -
            prbs {
                set ftInfo(event) $capture_PacketErrMap($ftVal)
                set ftInfo($capture_PacketErrMap($ftVal)) $ftVal
                set ftInfo(type) "standard"
            }
            pattern {
                if {[string match -nocase $eventType "trigger"]} {
                    set retVal "ERROR: \"pattern\" is not supported for triggers."
                    return 1
                }
                if {[string match -nocase $mode "add"]} {
                    set retVal "ERROR: \"pattern\" filter needs to have at least one pattern defined "
                    append retVal "as {-frameconfig <frame_config> -pdu <pdu> -field <pdu_field> -value <field_value>}. "
                    append retVal "Multiple patterns can be strung together with \"AND\" or \"OR\"."
                    return 1
                } else {
                    # we are removing the pattern
                    set ftInfo(event) "pattern"
                    set ftInfo(type) "pattern"
                    set ftInfo(pattern) ""
                }
            }
            length {
                if {[string match -nocase $mode "add"]} {
                    set retVal "ERROR: \"length\" filter or trigger needs to have a specified value "
                    append retVal "defined as {length <value>}."
                    return 1
                } else {
                    # we are removing the length
                    set ftInfo(event) "length"
                    set ftInfo(type) "length"
                    set ftInfo(length) 0
                }
            }
            default {
                set retVal "ERROR: \"-$eventType $ftVal\" possible values are: signature | oversize | jumbo "
                append retVal "| undersize | invalidfcs | ipCheckSum | oos | prbs | length <length> | pattern <pattern>"
                #if {[string match -nocase "pattern"]} {
                #    append retVal " | pattern <pattern>"
                #}
                return 1
            }
        }
    } elseif {$ltLength == 2} {
        set filtType [lindex $ftVal 0]
        set filtInfo [lindex $ftVal 1]

        switch -- [string tolower $filtType] {
            signature -
            oversize -
            jumbo -
            undersize -
            invalidfcs -
            ipCheckSum -
            oos -
            prbs {
                set retVal "ERROR: \"$filtType\" filter or trigger only takes the filter/trigger name as its argument."
                return 1
            }
            length {
                if {![string is integer $filtInfo] || ($filtInfo < 0) || ($filtInfo > 4294967295)} {
                    set retVal "ERROR: \"length\" filter or trigger must be an integer value <0-4294967295>."
                    return 1
                }
                set ftInfo(event) "length"
                set ftInfo(length) $filtInfo
                set ftInfo(type) "length"
            }
            pattern {
                set retVal ""
                if {[::sth::packetCapture::PacketCapture_ValidatePatternSequence $filtInfo retVal]} {
                    set retVal "ERROR: Failed to validate pattern: $retVal"
                    return 1
                }
                set ftInfo(event) "pattern"
                set ftInfo(pattern) $filtInfo
                set ftInfo(type) "pattern"
            }
            default {
                set retVal "ERROR: \"-$eventType $ftVal\" possible values are: signature | oversize | jumbo "
                append retVal "| undersize | invalidfcs | ipCheckSum | oos | prbs | length <length> | pattern <pattern>"
                #if {[string match -nocase "pattern"]} {
                #    append retVal " | pattern <pattern>"
                #}
                return 1
            }
        }
    } else {
        # If this is longer than 2, there must be multiple filters or triggers defined - this is an error
        set retVal "ERROR: \"-$eventType $ftVal\" possible values are: signature | oversize | jumbo "
        append retVal "| undersize | invalidfcs | ipCheckSum | oos | prbs | length <length> | pattern <pattern>"
        #if {[string match -nocase "pattern"]} {
        #    append retVal " | pattern <pattern>"
        #}
        append retVal "  Multiple filters or triggers can be defined by calling the command multiple times."
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_ValidatePatternSequence
#  Inputs:  pattern - pattern to validate
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Validate the users' pattern string.
#  Pattern should be defined as a list of lists that are anded or ored together:
#  {{-frameconfig ethernetii:ipv4 -pdu ipv4 -field sourceAddr -value 192.1.1.1} AND 
#            {-frameconfig ethernetii:ipv4 -pdu ipv4 -field destAddr -value 192.1.2.1}}
###
proc ::sth::packetCapture::PacketCapture_ValidatePatternSequence {pattern rvName} {
    variable capture_PduList
    variable capture_LogicalOps
    upvar 1 $rvName retVal

    set retVal ""

    # A pattern should be an alternating list of pattern strings and logical operators.  The first item in the
    # pattern should be the first pattern string followed by a logical operator and so on.  "parsingObj" will
    # keep track of what we should be parsing.
    set parsingObj "pattern"

    foreach item $pattern {
        # "item" is either a pattern (attr val list of -frameconfig -pdu -field -value) or
        # a logical operator &&, AND, OR, ||
        if {[string match -nocase $parsingObj "pattern"]} {
            # Validate "item" as a pattern
            set patternValMsg ""
            set parsedPattern ""

            if {[::sth::packetCapture::PacketCapture_ValidatePattern $item "patternValMsg"]} {
                set retVal "ERROR: \"pattern\" filter or trigger needs to have at least one pattern defined as "
                append retVal "{-frameconfig <frame_config> -pdu <pdu> -field <pdu_field> -value <field_value>}: "
                append retVal "$patternValMsg"
                return 1
            }
            # We expect an operator next.
            set parsingObj "operator"
        } else {
            # Validate "item" as an operator
            if {![info exists capture_LogicalOps([string tolower $item])]} {
                set retVal "ERROR: \"pattern\" filter or trigger is defined incorrectly.  "
                append retVal "Operator to connect patterns must be either \"AND\" or \"OR\"."
                return 1
            }
            # We should expect a pattern next.
            set parsingObj "pattern"
        }
    }
    return 0
}


###
#  Name:    PacketCapture_ValidatePattern
#  Inputs:  pattern - pattern string to validate (no operators - single pattern)
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Validate the users' pattern string.
#  Pattern should be defined as a list of lists that are anded or ored together:
#  {-frameconfig ethernetii:ipv4 -pdu ipv4 -field destAddr -value 192.1.2.1}
###
proc ::sth::packetCapture::PacketCapture_ValidatePattern {pattern rvName} {
    variable capture_PduList
    upvar 1 $rvName retVal
    set retVal ""

    array unset filterArgs
    array set filterArgs ""

    foreach {attr val} $pattern {
        set filterArgs([string tolower $attr]) $val
    }
    # Filter must be defined with -frameconfig -pdu -field -value
    if {![info exists filterArgs(-frameconfig)] || ![info exists filterArgs(-pdu)] || \
            ![info exists filterArgs(-field)] || ![info exists filterArgs(-value)]} {
        set retVal "ERROR: Pattern should be defined as {-frameconfig <frame_config> -pdu <pdu> -field <pdu_field>. "
        append retVal "-value <field_value>}."
        return 1
    }
    # Frame Config must be defined with existing PDUs.
    foreach pdu [split $filterArgs(-frameconfig) ":"] {
        if {![info exists capture_PduList([string tolower $pdu])]} {
            set retVal "ERROR: -frameconfig should be defined as <pdu1>:<pdu2>:<pdu3>:...<pduN> "
            append retVal "where <pduX> is one of: $capture_PduList(all)."
            return 1
        }
    }
    # PDU may have a number indicating which PDU the value applies to.  Will be separated from PDU name
    # by a colon.  Ie. "vlan:2" would be the inner VLAN.  "vlan:1" or "vlan" would be the outer 
    # (closer to ethernet header) VLAN.  We need to validate this string
    set splitPdu [split $filterArgs(-pdu) :]

    # PDU should have at most two elements when split on the colon
    if {[llength $splitPdu] > 2} {
        set retVal "ERROR: -pdu should be in the format <pdu>:\[index\]"
        return 1
    }
    set pduName [lindex $splitPdu 0]
    set pduIndex [lindex $splitPdu 1]

    # PDU should exist
    if {![info exists capture_PduList($pduName)]} {
        set retVal "ERROR: -pdu should be one of: $capture_PduList(all)."
        return 1
    }

    # PDU "index" should be an integer if it exists.
    if {($pduIndex != "") && ![string is integer $pduIndex]} {
        set retVal "ERROR: PDU index <pdu>:\[index\] should be an integer where 1 indicates outermost"
        append retVal " occurrance of the PDU."
        return 1
    }

    # PDU "index" should reference a PDU in the frameconfig
    if {($pduIndex != "")} {
        if {$pduIndex <= 0} {
            set retVal "ERROR: PDU index should be 1 or greater."
            return 1
        } else {
            set pduCount 0
            foreach fcPdu [split $filterArgs(-frameconfig) ":"] {
                if {[string match -nocase $fcPdu $pduName]} {
                    incr pduCount
                }
            }
            if {$pduIndex > $pduCount} {
                set retVal "ERROR: PDU index $pduIndex is out of range of the number of $pduName PDUs in the -frameconfig."
                return 1
            }
        }
    } else {
        if {[lsearch [split $filterArgs(-frameconfig) ":"] $pduName] == -1} {
            set retVal "ERROR: -pdu \"$filterArgs(-pdu)\" should appear in the frame config defined in -frameconfig."
            return 1
        }
    }

    # Field
    # Validate the field in the given PDU
    if {![info exists capture_PduList($pduName,$filterArgs(-field))]} {
        set retVal "ERROR: -field \"$filterArgs(-field)\" in $pduName not recognized.  "
        append retVal "Should be one of $capture_PduList($pduName,all)."
        return 1
    }

    # Value
    # Validate the value of the given field in the given PDU.
    switch -- $capture_PduList($pduName,$filterArgs(-field),verify) {
        mac {
            if {![::sth::packetCapture::MacVerify $filterArgs(-value)]} {
                set retVal "ERROR: -value \"$filterArgs(-value)\" in $pduName $filterArgs(-field) should be"
                append retVal " a valid MAC address."
                return 1
            }
        }
        ip {
            if {![::sth::packetCapture::IpVerify $filterArgs(-value)]} {
                set retVal "ERROR: -value \"$filterArgs(-value)\" in $pduName $filterArgs(-field) should be"
                append retVal " a valid IP address."
                return 1
            }
        }
        ipv6 {
            if {![::sth::packetCapture::Ipv6Verify $filterArgs(-value)]} {
                set retVal "ERROR: -value \"$filterArgs(-value)\" in $pduName $filterArgs(-field) should be"
                append retVal " a valid IPv6 address."
                return 1
            }
        }
        int {
            if {![regexp {^[0-9]+$} $filterArgs(-value)]} {
                set retVal "ERROR: -value \"$filterArgs(-value)\" in $pduName $filterArgs(-field) should be"
                append retVal " a valid integer."
                return 1
            }
        }
        hex {
            if {![regexp {^[0-9a-fA-F]+$} $filterArgs(-value)]} {
                set retVal "ERROR: -value \"$filterArgs(-value)\" in $pduName $filterArgs(-field) should be"
                append retVal " a valid hexadecimal string."
                return 1
            }
        }
        none -
        default {
            # No verification here, let everything through
        }
    }
    return 0
}


###
#  Name:    PacketCapture_ProcessStandardEvents
#  Inputs:  portHandleList - list of port handles to configure standard events (no arguments)
#           stdStcEvents - list of standard events
#           eventType - event | startevent | stopevent
#           mode - add | remove
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Configure standard events for the given condition
###
proc ::sth::packetCapture::PacketCapture_ProcessStandardEvents {portHandleList stdStcEvents eventType mode rvName} {
    upvar 1 $rvName retVal
    set retVal ""
    set eventState "IGNORE"
    # Since we don't know if other triggers are still active (well, we could check but is it really necessary?) just
    # never turn off eventSwitch once start/stop/qualify events have been enabled.
    set eventSwitch "TRUE"
    if {[string match [string tolower $mode] "add"]} {
        set eventState "INCLUDE"
        set eventSwitch "TRUE"
    }
    # Get Proxy IDs
    set proxyIDList ""
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandleList proxyIDList]} {
        set retVal "ERROR: Failed to get capture objects from under port(s): $portHandleList."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    # Configure either Capture Filters, Start Events, or Stop Events
    foreach proxyID $proxyIDList {
        set switchAttr ""
        set debugTxt ""
        switch -- $eventType {
            "event" {
                # Configure Capture Filter
                set debugTxt "capture filter"
                set filtObj "CaptureFilter"
                set switchAttr "QualifyEvents"
            }
            "startevent" {
                # Configure Capture Filter Start Event
                set debugTxt "capture filter start event"
                set filtObj "CaptureFilterStartEvent"
                set switchAttr "StartEvents"
            }
            "stopevent" {
                # Configure Capture Filter Stop Event
                set debugTxt "capture filter stop event"
                set filtObj "CaptureFilterStopEvent"
                set switchAttr "StopEvents"
            }
        }
        # Get specified Capture Object
        if {[catch {set captureObjID [::sth::sthCore::invoke stc::get $proxyID -children-$filtObj]} errMsg]} {
            set retVal "ERROR: Failed to get $debugTxt object from under $proxyID: $errMsg"
            return 1
        }
        # Configure Capture Object
        if {[catch {sth::sthCore::invoke stc::config $captureObjID [list -$stdStcEvents $eventState -$switchAttr $eventSwitch]} errMsg]} {
            set retVal "ERROR: Failed to configure $debugTxt $captureObjID: $errMsg."
            return 1
        }
    }
    return 0
}


###
#  Name:    PacketCapture_ProcessLength
#  Inputs:  portHandleList - list of port handles to configure standard events (no arguments)
#           length - integer packet length value
#           eventType - event | startevent | stopevent
#           mode - add | remove
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Configure packet length events for the given condition
###
proc ::sth::packetCapture::PacketCapture_ProcessLength {portHandleList length eventType mode rvName} {
    upvar 1 $rvName retVal
    set retVal ""

    # Get Proxy IDs
    set proxyIDList ""
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandleList proxyIDList]} {
        set retVal "ERROR: Failed to get capture objects from under port(s): $portHandleList."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    # Configure either Capture Filters, Start Events, or Stop Events
    foreach proxyID $proxyIDList {
        set debugTxt ""
        switch -- $eventType {
            "event" {
                # Configure Capture Filter
                set debugTxt "capture filter"
                set filtObj "CaptureFilter"
            }
            "startevent" {
                # Configure Capture Filter Start Event
                set debugTxt "capture filter start event"
                set filtObj "CaptureFilterStartEvent"
            }
            "stopevent" {
                # Configure Capture Filter Stop Event
                set debugTxt "capture filter stop event"
                set filtObj "CaptureFilterStopEvent"
            }
        }
        # Get specified Capture Object
        if {[catch {set captureObjID [::sth::sthCore::invoke stc::get $proxyID -children-$filtObj]} errMsg]} {
            set retVal "ERROR: Failed to get $debugTxt object from under $proxyID: $errMsg"
            return 1
        }
        # Configure Capture Object
        if {[string match -nocase $mode "add"]} {
            if {[catch {sth::sthCore::invoke stc::config $captureObjID [list -FrameLenMatch "INCLUDE" -FrameLength $length]} errMsg]} {
                set retVal "ERROR: Failed to configure $debugTxt frame length under $captureObjID: $errMsg."
                return 1
            }
        } else {
            if {[catch {sth::sthCore::invoke stc::config $captureObjID [list -FrameLenMatch "IGNORE"]} errMsg]} {
                set retVal "ERROR: Failed to configure $debugTxt frame length under $captureObjID: $errMsg."
                return 1
            }
        }
    }
    return 0
}


###
#  Name:    PacketCapture_ProcessPatternSequence
#  Inputs:  portHandleList - list of port handles to configure standard events (no arguments)
#           pattern - sequence of patterns linked together by logical operators
#           mode - add | remove
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Configure pattern events for the given condition
#  Note:    Only applicable for filters (not for triggers)
###
proc ::sth::packetCapture::PacketCapture_ProcessPatternSequence {portHandleList pattern mode rvName} {
    upvar 1 $rvName retVal
    set retVal ""

    # Get Proxy IDs
    set proxyIDList ""
    if {[::sth::packetCapture::PacketCapture_GetCaptureProxyID $portHandleList proxyIDList]} {
        set retVal "ERROR: Failed to get capture objects from under port(s): $portHandleList."
        ::sth::sthCore::log debug $retVal
        return 1
    }
    # Configure either Capture Filters, Start Events, or Stop Events
    foreach proxyID $proxyIDList {
        set addStatus ""
        if {[string match -nocase $mode "add"]} {
            # Need to remove all currently defined patterns first
            if {[::sth::packetCapture::PacketCapture_RemovePatternSequence $proxyID removeStatus]} {
                lappend retVal "ERROR: Failed to clear out previously defined pattern(s): $removeStatus"
            }
            if {[::sth::packetCapture::PacketCapture_AddPatternSequence $proxyID $pattern addStatus]} {
                lappend retVal $addStatus
            }
        } else {
            # Remove ALL patterns defined under this capture filter
            set removeStatus ""
            if {[::sth::packetCapture::PacketCapture_RemovePatternSequence $proxyID removeStatus]} {
                lappend retVal $removeStatus
            }
        }
    }
    if {$retVal != ""} {
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_AddPatternSequence
#  Inputs:  proxyID - a capture object ID (STC object)
#           pattern - sequence of patterns linked together by logical operators
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Parse the given pattern and add it to the capturefilter under the given proxyID.
#  Note:    Only applicable for filters (not for triggers)
###
proc ::sth::packetCapture::PacketCapture_AddPatternSequence {proxyID pattern rvName} {
    upvar 1 $rvName retVal
    # Get Capture Filter ID
    set errMsg ""
    if {[catch {set captureFiltID [::sth::sthCore::invoke stc::get $proxyID -children-CaptureFilter]} errMsg]} {
        lappend retVal "ERROR: Failed to get Capture Filter object from under $proxyID: $errMsg"
        return 1
    }
    # Process the pattern in a manner similar to how it was validated -
    # Pattern should be alternating sequence of patterns and operators.
    set parsingObj "pattern"
    array unset pInfo
    array set pInfo ""
    foreach item $pattern {
        if {$parsingObj == "pattern"} {
            # We will actually create the object after we get the operator that connects it to the next one.
            # If there is a single pattern defined (with no operators) we will set everything up and check
            # (outside this loop) if parsingObj is set to "operator."  Operator will default to "AND" if there
            # is a single pattern defined in this sequence.
            array set pInfo $item
            set parsingObj "operator"
        } elseif {$parsingObj == "operator"} {
            # Create the object
            set cafStatus ""
            if {[::sth::packetCapture::PacketCapture_CreateCaptureAnalyzerFilter $captureFiltID \
                     $pInfo(-frameconfig) $pInfo(-pdu) $pInfo(-field) $pInfo(-value) $item cafStatus pInfo]} { 
                lappend retVal "ERROR: Failed to create Filter on $proxyID: $cafStatus"
                array unset pInfo
                break
            }
            array unset pInfo
            set parsingObj "pattern"
        }
    }
    # Need to create the last pattern if multiple patterns were specified (ie the fencepost problem)
    if {$parsingObj == "operator"} {
        # Create the object
        set cafStatus ""
        if {[::sth::packetCapture::PacketCapture_CreateCaptureAnalyzerFilter $captureFiltID \
                 $pInfo(-frameconfig) $pInfo(-pdu) $pInfo(-field) $pInfo(-value) "AND" cafStatus pInfo]} { 
            lappend retVal "ERROR: Failed to create Filter on $proxyID: $cafStatus"
            array unset pInfo
        }
        array unset pInfo
    }
    return 0
}


###
#  Name:    PacketCapture_RemovePatternSequence
#  Inputs:  proxyID - a capture object ID (STC object)
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Remove all patterns under given capture proxy ID.
#           Removing such objects is FINAL and IRREVERSIBLE.
#  Note:    Only applicable for filters (not for triggers)
###
proc ::sth::packetCapture::PacketCapture_RemovePatternSequence {proxyID rvName} {
    upvar 1 $rvName retVal
    # Get Capture Filter ID
    set errMsg ""
    if {[catch {set captureFiltID [::sth::sthCore::invoke stc::get $proxyID -children-CaptureFilter]} errMsg]} {
        set retVal "ERROR: Failed to get Capture Filter object from under $proxyID: $errMsg"
        return 1
    }
    # Get all of the CaptureAnalyzerFilter objects under the CaptureFilter
    if {[catch {set cafList [::sth::sthCore::invoke stc::get $captureFiltID -children-CaptureAnalyzerFilter]} errMsg]} {
        set retVal "ERROR: Failed to get CaptureAnalyerFilter objects from under $captureFiltID: $errMsg"
        return 1
    }
    # Delete the objects
    set failedObjs ""
    foreach cafID $cafList {
        if {[catch {sth::sthCore::invoke stc::delete $cafID} errMsg]} {
            lappend failedObjs $cafID
            continue
        }
    }
    if {$failedObjs != ""} {
        set retVal "ERROR: Failed to delete $failedObjs objects from under $captureFiltID: $errMsg"
        return 1
    }
    return 0
}


###
#  Name:    PacketCapture_CreateCaptureAnalyzerFilter
#  Inputs:  captureFiltID - capturefilter ID (STC object)
#           frameconfig - list of pdus joined by colon (:), ie ethernetii:ipv4
#           pdu - single pdu (ie ethernetii or arp) with the option to indicate which one (using the colon)
#           field - field value inside pdu (ie senderpaddr in arp pdu)
#           value - value for the given field (ie 192.1.1.1)
#           relationToNext - AND | OR, relation to the next pattern.
#           rvName - name of the return variable (for error messages)
#  Globals: none.
#  Outputs: 0 | 1 - pass | fail
#  Description: Create capture analyzer filter to filter on a given pattern
#  Note:    Only applicable for filters (not for triggers)
###
proc ::sth::packetCapture::PacketCapture_CreateCaptureAnalyzerFilter {captureFiltID frameConfig pdu field \
                                                                          value relationToNext rvName patternAttr} {
    upvar 1 pInfo $patternAttr
    variable capture_PduList
    upvar 1 $rvName retVal
    set errMsg ""
    set cafID ""
    
    set patternName "{}"
    if {[info exists pInfo(-pattern_name)]} {
        set patternName $pInfo(-pattern_name)
    }
    
    if {[catch {set cafID [::sth::sthCore::invoke stc::create "CaptureAnalyzerFilter" -under $captureFiltID "-FilterDescription $patternName"]} errMsg]} {
        set retVal "ERROR: Failed to create CaptureAnalyzerFilter under $captureFiltID: $errMsg"
        return 1
    }
    # Clear out the FrameConfig variable
    if {[catch {sth::sthCore::invoke stc::config $cafID -frameConfig ""} errMsg]} {
        set retVal "ERROR: Failed to clear out default frame config under $cafID: $errMsg"
        # Clean up here - delete CaptureAnalyzerFilter
        if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
            append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
        }
        return 1
    }
    # Rebuild the PDUs
    set pduName [lindex [split $pdu :] 0]
    set pduIndex [lindex [split $pdu :] 1]
    if {$pduIndex == ""} {
        set pduIndex 1
    }
    set stcCreatedPduCount 0
    
    foreach userPdu [split $frameConfig :] {
    	#puts $userPdu
        set stcPdu $capture_PduList($userPdu,stc)
        #puts "stcPdu $stcPdu"
        if {$stcPdu == "ipv4:DiffServByte"} {
            set pdutosDiffserv [::sth::sthCore::invoke stc::create tosDiffserv -under $pduObj]
            set pduObj [::sth::sthCore::invoke stc::create Diffserv -under $pdutosDiffserv]
        } elseif {$stcPdu != "ethernet:Vlan"} {   
	        if {[catch {set pduObj [::sth::sthCore::invoke stc::create $stcPdu -under $cafID]} errMsg]} {
	            set retVal "ERROR: Failed to create PDU $userPdu ($stcPdu) under FrameConfig in $captureFiltID ($cafID): $errMsg"
	            # Clean up here - delete CaptureAnalyzerFilter
	            if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
	                append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
	            }
	            return 1
	        }
        } else {
                if {[set pduVlans [::sth::sthCore::invoke stc::get $cafID.ethernet:EthernetII -children-vlans]] == ""} {
                    if {[catch {set pduObj [::sth::sthCore::invoke stc::create "vlans" -under $pduObj]} errMsg]} {
                        set retVal "ERROR: Failed to create PDU $userPdu ($stcPdu) under FrameConfig in $captureFiltID ($cafID): $errMsg"
                        # Clean up here - delete CaptureAnalyzerFilter
                        if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
                            append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
                        }
                        return 1
                    }
                } else {
                    set pduObj $pduVlans
                }
	        
	        if {[catch {set pduObj [::sth::sthCore::invoke stc::create "Vlan" -under $pduObj]} errMsg]} {
	            set retVal "ERROR: Failed to create PDU $userPdu ($stcPdu) under FrameConfig in $captureFiltID ($cafID): $errMsg"
	            # Clean up here - delete CaptureAnalyzerFilter
	            if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
	                append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
	            }
	            return 1
	        }
        }
        
        
        set attribute [::sth::sthCore::invoke stc::get $pduObj]
        #puts $attribute
        set  pduObjs [::sth::sthCore::invoke stc::get $pduObj -children]
        #puts "$pduObj children $pduObjs"
        
        if {[string match -nocase $pduName $userPdu]} {
            incr stcCreatedPduCount
        }
        if {[string match -nocase $pduName $userPdu] && ($pduIndex == $stcCreatedPduCount)} {
            # Configure the value
            #The user_priority field is of type bits. Need to make a transformation here
            if {$field == "pri"} {
               set value $::sth::Traffic::arrayDecimal2Bin($value);
            }
            if {[catch {::sth::sthCore::invoke stc::config $pduObj -$field $value} errMsg]} {
                set retVal "ERROR: Failed to configure PDU $userPdu ($stcPdu) field $field with $value: $errMsg"
                # Clean up here - delete this CaptureAnalyzerFilter
                if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
                    append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
                }
                return 1
            }
            # Configure the value to be matched and the relation to the next filter.
            if {[catch {::sth::sthCore::invoke stc::config $cafID -ValueToBeMatched $value -RelationToNextFilter $relationToNext} errMsg]} {
                set retVal "ERROR: Failed to configure $cafID (-ValueToBeMatched $value -RelationToNextFilter $relationToNext) "
                append retVal "in $cafID: $errMsg"
                # Clean up here - delete this CaptureAnalyzerFilter
                if {[catch {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
                    append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
                }
                return 1
            }
        }
    }
    # Hack:
    # We need to save the captureanalyzerfilter's "-frameconfig" value and reset -frameconfig back to it
    # so that the BLL realizes the PDUs have been properly set.
    if {[catch {set pduConfig [::sth::sthCore::invoke stc::get $cafID -frameconfig]} errMsg]} {
        ::sth::sthCore::log error $erMsg
        set retVal $errMsg
        return 1
    }
    if {[catch {sth::sthCore::invoke stc::config $cafID -frameConfig $pduConfig} errMsg]} {
        ::sth::sthCore::log error $erMsg
        set retVal $errMsg
        return 1
    }

	#puts "pduConfig ---> $pduConfig"
	

    # Finally, enable this CaptureAnalyzerFilter
    if {[catch {::sth::sthCore::invoke stc::config $cafID -IsSelected 1} errMsg]} {
        set retVal "ERROR: Failed to enable $cafID."
        # Clean up here - delete this CaptureAnalyzerFilter
        if {[capture {::sth::sthCore::invoke stc::delete $cafID} errMsg]} {
            append retVal "  Clean up - ERROR: Failed to delete $caf: $errMsg"
        }
        return 1
    }
    return 0
}



####################################
#
#   Utility Procs
#
####################################
#
# Eventually these should be moved to a general area.


###
#  Name: IntToHex
#  Inputs:  integer
#  Globals: none
#  Outputs: hex
#  Description: Changes an integer into a hexadecimal number
###
proc ::sth::packetCapture::IntToHex {int {length 1}} {
    return [format "%0${length}x" $int]
}


###
#  Name: HexToInt
#  Inputs:  hex number
#  Globals: none
#  Outputs: integer
#  Description: Changes hex to an integer
###
proc ::sth::packetCapture::HexToInt {hex} {
    set total 0.0
    set fullhex $hex
    if {[string first 0x $fullhex] != -1} {
        set fullhex [string range $fullhex 2 end]
    } elseif {[string first h $fullhex] != -1} {
        set fullhex [string range $fullhex 0 end-1]
    }
    set numLongs [expr {[string length $fullhex] / 8}]
    if {[expr {[string length $fullhex] % 8}] != 0} {incr numLongs}

    for {set i 0} {$i < $numLongs} {incr i} {
        set start [expr {$i * 8}]
        set end [expr {$start + 7}]
        set hex [string range $fullhex $start $end]
        if {[string first 0x $hex] != -1} {
            set hex [string range $hex 2 end]
        } elseif {[string first h $hex] != -1} {
            set hex [string range $hex 0 end-1]
        }
        set temp [format "%u" 0x${hex}]
        set total [expr {$total + "$temp.0"}]
    }

    set total [string range $total 0 [expr {[string first . $total] - 1}]]

    return $total
}


###
#  Name: IpVerify
#  Inputs:  val - (ipv4 address)
#  Globals: None
#  Outputs: 0 - Address is not IPv4
#           1 - IP is an IPv4 address
#  Description: Checks if a string is a valid ip address.
###
proc ::sth::packetCapture::IpVerify {ip} {
    if {[llength [split $ip .]] < 4 || [llength [split $ip .]] > 4} {
        return 0
    }
    foreach ipw [split $ip .] {
        if {[catch {expr {$ipw > 255 || $ipw < 0}} ret] || $ret == 1} {
            return 0
        }
    }
    return 1
}


###
#  Name: Ipv6Verify
#  Inputs:  ip - ip address
#  Globals: none
#  Outputs: 0 - invalid
#           1 - valid
#  Description: Returns 1 if the value is a valid IPv6 formatted address.
###
proc ::sth::packetCapture::Ipv6Verify {ip} {
    if {[string first : $ip] == -1} { return 0 }

    set ip [::sth::packetCapture::Ipv6Expand $ip]
    if {[llength [split $ip :]] != 8} {
        return 0
    }

    foreach ipw [split $ip :] {
        if {[catch {expr {[HexToInt $ipw] > 0xFFFF || [HexToInt $ipw] < 0}} ret] || $ret == 1} {
            return 0
        }
    }

    return 1
}


###
#  Name: Ipv6Expand
#  Inputs:  ip - ipv6 address
#  Globals: none
#  Outputs: ipv6 address
#  Description: Returns an IPv6 address in the following format:
#     <xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx>
###
proc ::sth::packetCapture::Ipv6Expand {ip} {
    # handle special cases (i.e., ::1, 1::, or ::)
    if {[string index $ip 0] == ":"} {
        set ip "0$ip"
    }
    if {[string index $ip end] == ":"} {
        set ip "${ip}0"
    }
    set ip  [split $ip :]
    set len [llength $ip]
    set val {}
    foreach word $ip {
        if {[llength $word] == 0} {
            # found a zero compressed address ("::") that needs padding
            set pad [expr {9 - $len}]
            for {set i 0} {$i < $pad} {incr i} {
                lappend val [string repeat 0 4]
            }
        } else {
            lappend val [format %04X 0x$word]
        }
    }
    return [join $val :]
}


###
#  Name: MacVerify
#  Inputs:  val (mac address)
#  Outputs: 0 - string is not a mac
#           1 - string is a mac
#  Globals: None
#  Description: Checks if a string is a valid mac address.
###
proc ::sth::packetCapture::MacVerify {mac} {

    if {[llength [split $mac .]] < 6 || [llength [split $mac .]] > 6} {
        if {[llength [split $mac :]] < 6 || [llength [split $mac :]] > 6} {
            return 0
        } else {
            set split :
        }
    } else {
        set split .
    }

    foreach byte [split $mac $split] {
        if {[regexp {[g-zG-Z]} $byte]} {
            return 0
        } else {
            if {[string length $byte] > 2} {
                return 0
            }
        }

    }

    return 1
}
