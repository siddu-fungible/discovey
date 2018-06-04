----------------------------------------
-- script-name: FCP.lua
--
-- author: Amit Surana <amit.surana at fungible dot com>
-- Copyright (c) 2018, Amit Surana


local debug_level = {
    DISABLED = 0,
    LEVEL_1  = 1,
    LEVEL_2  = 2
}

local DEBUG = debug_level.LEVEL_1

local default_settings =
{
    debug_level  = DEBUG,
    port         = 65333,
    heur_enabled = false,
}

local args={...} -- get passed-in args
if args and #args > 0 then
    for _, arg in ipairs(args) do
        local name, value = arg:match("(.+)=(.+)")
        if name and value then
            if tonumber(value) then
                value = tonumber(value)
            elseif value == "true" or value == "TRUE" then
                value = true
            elseif value == "false" or value == "FALSE" then
                value = false
            elseif value == "DISABLED" then
                value = debug_level.DISABLED
            elseif value == "LEVEL_1" then
                value = debug_level.LEVEL_1
            elseif value == "LEVEL_2" then
                value = debug_level.LEVEL_2
            else
                error("invalid commandline argument value")
            end
        else
            error("invalid commandline argument syntax")
        end

        default_settings[name] = value
    end
end

local dprint = function() end
local dprint2 = function() end
local function reset_debug_level()
    if default_settings.debug_level > debug_level.DISABLED then
        dprint = function(...)
            print(table.concat({"Lua:", ...}," "))
        end

        if default_settings.debug_level > debug_level.LEVEL_1 then
            dprint2 = dprint
        end
    end
end
reset_debug_level()

dprint2("Wireshark version = ", get_version())
dprint2("Lua version = ", _VERSION)

local major, minor, micro = get_version():match("(%d+)%.(%d+)%.(%d+)")
if major and tonumber(major) <= 1 and ((tonumber(minor) <= 10) or (tonumber(minor) == 11 and tonumber(micro) < 3)) then
        error(  "Sorry, but your Wireshark/Tshark version ("..get_version()..") is too old for this script!\n"..
                "This script needs Wireshark/Tshark version 1.11.3 or higher.\n" )
end

assert(ProtoExpert.new, "Wireshark does not have the ProtoExpert class, so it's too old - get the latest 1.11.3 or higher")


fcp_protocol = Proto("FUN_FCP",  "Fungible FCP Protocol")

fcp_protocol.fields = {}

local ver             = ProtoField.uint8("FUN_FCP.version", "Version", base.HEX, nil, 0xC0)

local types = {
        [0] = "Request",
        [1] = "Grant",
        [2] = "Data",
        [3] = "Control"
}
local type            = ProtoField.uint8("FUN_FCP.type", "Type", base.HEX, types, 0x38)

local protocols = {
        [0] = "No Payload",
        [1] = "IPv4",
        [2] = "IPv6"
}
local next_proto      = ProtoField.uint8("FUN_FCP.next_proto", "NextProtocol", base.HEX, protocols, 0x07)

local rsvd            = ProtoField.uint8("FUN_FCP.rsvd", "Reserved", base.HEX, nil, 0xF0)
local flags           = ProtoField.uint8("FUN_FCP.flags", "Flags", base.HEX, nil, 0x0F)
local flags_security  = ProtoField.new("Security", "FUN_FCP.flags.security", ftypes.BOOLEAN, nil, 8, 0x01) 
local flags_timestamp = ProtoField.new("Timestamp", "FUN_FCP.flags.timestamp", ftypes.BOOLEAN, nil, 8, 0x02)
local gphs = {
        [0] = "GPH 0B",
        [1] = "GPH 4B",
        [2] = "GPH 8B",
        [3] = "GPH 16B"
}
local flags_gph       = ProtoField.uint8("FUN_FCP.flags.gph", "GPH", base.HEX, gphs, 0x0C)

local tunnel_num      = ProtoField.uint16("FUN_FCP.tunnel", "Tunnel Number", base.DEC, nil)
local queue           = ProtoField.uint8("FUN_FCP.queue", "Queue Num", base.DEC, nil)

local weight          = ProtoField.uint8("FUN_FCP.weight", "Weight", base.DEC, nil)
local scale           = ProtoField.uint8("FUN_FCP.scale_factor", "Scale Factor", base.DEC, nil)

local rbn             = ProtoField.uint16("FUN_FCP.rbn", "Request Block Number", base.DEC, nil)
local gbn             = ProtoField.uint16("FUN_FCP.gbn", "Grant Block Number", base.DEC, nil)
local dbn             = ProtoField.uint16("FUN_FCP.dbn", "Data Block Number", base.DEC, nil)

local data_seq_num    = ProtoField.uint24("FUN_FCP.seq_num", "Data Seq Num", base.DEC, nil)

local gph_4b          = ProtoField.uint32("FUN_FCP.gph", "GPH Marix", base.HEX, nil)
local gph_8b          = ProtoField.uint64("FUN_FCP.gph", "GPH Marix", base.HEX, nil)
local timestamp       = ProtoField.uint32("FUN_FCP.timestamp", "Timestamp", base.DEC, nil)

local spi     		  = ProtoField.uint8("FUN_FCP.spi", "Security SPI", base.DEC, nil)
local alen            = ProtoField.uint8("FUN_FCP.alen", "Security Alen", base.DEC, nil)
local iv_0 		   	  = ProtoField.uint24("FUN_FCP.iv0", "Security IV0", base.DEC, nil)
local iv_1			  = ProtoField.uint24("FUN_FCP.iv1", "Security IV1", base.DEC, nil)
local icv_0 		  = ProtoField.uint24("FUN_FCP.icv0", "Security ICV0", base.DEC, nil)
local icv_1			  = ProtoField.uint24("FUN_FCP.icv1", "Security ICV1", base.DEC, nil)

fcp_protocol.fields = { ver, type, next_proto, rsvd, flags, flags_security, flags_timestamp,
                        flags_gph, tunnel_num, queue, weight, scale, rbn, gbn, dbn,
                        data_seq_num, gph_4b, gph_8b, timestamp, spi, alen, iv_0, iv_1,
                        icv_0, icv_1 }

local type_val            = Field.new("FUN_FCP.type")
local protocol_val        = Field.new("FUN_FCP.next_proto")
local flags_security_val  = Field.new("FUN_FCP.flags.security")
local flags_timestamp_val = Field.new("FUN_FCP.flags.timestamp")
local flags_gph_val       = Field.new("FUN_FCP.flags.gph")

local function get_type() return type_val()() end
local function get_protocol() return protocol_val()() end
local function is_secure() return flags_security_val()() end
local function is_timestamped() return flags_timestamp_val()() end
local function get_gph() return flags_gph_val()() end
    
function fcp_protocol.dissector(buffer, pinfo, tree)
  length = buffer:len()
  if length == 0 then return end

  pinfo.cols.protocol = fcp_protocol.name

  local subtree = tree:add(fcp_protocol, buffer(), "FCP Protocol Data")
   
  subtree:add(ver,              buffer(0,1))
  subtree:add(type,             buffer(0,1))
  subtree:add(next_proto,       buffer(0,1))
  
  local flags_subtree = subtree:add(fcp_protocol, buffer(), "Flags")
  
  flags_subtree:add(rsvd,             buffer(1,1))
  flags_subtree:add(flags_security,   buffer(1,1))
  flags_subtree:add(flags_timestamp,  buffer(1,1))
  flags_subtree:add(flags_gph,        buffer(1,1))
  
  -- subtree:add(rsvd,             buffer(1,1))
  -- subtree:add(flags_security,   buffer(1,1))
  -- subtree:add(flags_timestamp,  buffer(1,1))
  -- subtree:add(flags_gph,        buffer(1,1))
  subtree:add(tunnel_num, 		buffer(2,2))
  subtree:add(queue,      		buffer(4,1))
  
  local type_value = get_type()
  info("type is:" .. type_value)
  if type_value == 0 then
    pinfo.cols.info = "FCP REQUEST"
  	subtree:add(weight,  buffer(5,1))
  	subtree:add(rbn, buffer(6,2))
  	buf_index = 8
  elseif type_value == 1 then
    pinfo.cols.info = "FCP GRANT"
    subtree:add(scale, buffer(5,1))
    subtree:add(gbn, buffer(6,2))
    buf_index = 8
   elseif type_value == 2 then
    pinfo.cols.info = "FCP DATA"
    subtree:add(data_seq_num, buffer(5,3))
    subtree:add(dbn, buffer(8,2))
    buf_index = 10
  end
  
  local gph_val = get_gph()
  if gph_val ~= 0 then
    local gph_subtree = subtree:add(fcp_protocol, buffer(), "GPH Matrix")
    pinfo.cols.info:append(", with GPH")
    if gph_val == 1 then
      gph_subtree:add(gph_4b, buffer(buf_index,4))
      buf_index = buf_index + 4
    elseif gph_val == 2 then
      gph_subtree:add(gph_8b, buffer(buf_index,8))
      buf_index = buf_index + 8
    end
  end
  
  if is_timestamped() then
    pinfo.cols.info:append(", with TS")
    local ts_subtree = subtree:add(fcp_protocol, buffer(), "Time Stamp")
    ts_subtree:add(timestamp, buffer(buf_index,4))
    buf_index = buf_index + 4
  end
  
  if is_secure() then
    pinfo.cols.info:append(", with SECURITY")
    local sec_subtree = subtree:add(fcp_protocol, buffer(), "Security")
    sec_subtree:add(spi, buffer(buf_index,1))
    buf_index = buf_index + 1
    sec_subtree:add(alen, buffer(buf_index, 1))
    buf_index = buf_index + 1
    sec_subtree:add(iv_0, buffer(buf_index, 3))
    buf_index = buf_index + 2
    sec_subtree:add(iv_1, buffer(buf_index, 3))
    buf_index = buf_index + 3
    sec_subtree:add(icv_0, buffer(buf_index, 3))
    buf_index = buf_index + 3
    sec_subtree:add(icv_1, buffer(buf_index, 3))
    buf_index = buf_index + 3
  end
  
  local protocol_value = get_protocol()
  if protocol_value == 1 then
    local ipv4_dis = Dissector.get("ip")
    ipv4_dis:call(buffer(buf_index):tvb(), pinfo, tree)
  elseif protocol_value == 2 then
    local ipv6_dis = Dissector.get("ipv6")
    ipv6_dis:call(buffer(buf_index):tvb(), pinfo, tree)
  end
end
  
local tcp_port = DissectorTable.get("udp.port")
tcp_port:add(57005, fcp_protocol)



