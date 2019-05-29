#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018 Bluecat Networks Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# B.Shorland - BlueCat Networks

import itertools
import random
import netaddr
from inspect import getmembers
from pprint import pprint
# import httplib
from suds.client import Client
from suds import WebFault
from suds.transport.http import HttpAuthenticated
from pip._vendor.ipaddress import ip_address
import logging as log

class bcolours:

    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


bam_address = "172.17.7.11"
bam_api_user = "api"
bam_api_pass = "api"
bam_config_name = "RW300984"

def main():

    print (bcolours.BOLD + "Bluecat BAM Client Support Library" + bcolours.ENDC)
    print ( bcolours.GREEN + "[AWS Sync] BlueCat Address Manager: " + bcolours.ENDC +  bam_address )
    print ( bcolours.GREEN + "[AWS Sync] BlueCat Address Manager API User: " + bcolours.ENDC + bam_api_user )
    print ( bcolours.GREEN + "[AWS Sync] BlueCat Address Manager API Password: " + bcolours.ENDC + bam_api_pass )
    print ( bcolours.GREEN + "[AWS Sync] BlueCat Default Configuration Name: " + bcolours.ENDC + bam_config_name )
    soap_client = bam_login()
    configID = get_configid(soap_client,bam_config_name)
    x = GetBAMInfo(soap_client)
    print ("Bluecat Address Manager Hostname: " + getPropsField(x, "hostName"))
    print ("Bluecat Address Manager Version: " + getPropsField(x, "version"))
    print ("Bluecat Address Manager Configuration: " + str(configID))
    bam_logout(soap_client)

# ----------------------- Bluecat API Routines ------------------

def getItemsFromResponse(data):
    dataStr = data.decode("utf-8")
    words = dataStr.split(',')
    return words

def getPropsField(properties, keyName):
    propsArr = properties.split('|')
    for prop in propsArr:
        kv = prop.split("=")
        if kv[0] == keyName:
            return kv[1]
            break
    return None

def processProperties(properties):
    retProps = {}
    if properties == None:
    	return
    properties = properties.split("|")
    for entityProp in properties:
        if entityProp == "":
            continue
        entityProp = entityProp.split("=")
        retProps[entityProp[0]] = entityProp[1]
    return retProps

def updatePropsStr(props, fieldName, value):
    params = {}
    keyValPairs = props.split('|')
    for keyValPair in keyValPairs:
        keyVal = keyValPair.split('=')
        if len(keyVal) > 1:
            params[keyVal[0]] = keyVal[1]
    params[fieldName] = value
    newProps = ""
    for key in params:
        newProps += key +"=" +params[key] +'|'
    return newProps

def getValueFromDataStr(dataStr, counter):
    data = dataStr[0]
    fields = data.split(':')
    value = fields[1]
    return(value)

# Login to BAM
def bam_login():
   print (bcolours.GREEN + bcolours.BOLD + '[CloudAtlas] Connecting to BlueCat Address Manager: ' + bcolours.ENDC + bam_address )
   soap_client = Client('http://%s/Services/API?wsdl' % bam_address)
   soap_client.service.login(bam_api_user, bam_api_pass)
   return soap_client

# Logout of BAM
def bam_logout(soap_client):
   print (bcolours.GREEN + bcolours.BOLD + "[CloudAtlas]: Disconnecting from BlueCat Address Manager: " + bcolours.ENDC + bam_address )
   soap_client.service.logout()

# Return long of ID for a specific configuration passed
def get_configid(soap_client,config_name):
   configID = soap_client.service.getEntityByName(0, config_name, 'Configuration')['id']
   return configID

# Get BAM configs
def get_configs(soap_client,configs,start,count):
	configs = soap_client.service.searchByObjectTypes(configs,"Configuration",start,count)
	return configs[0]

def GetNetworkV6(soap_client,configID,IP6):
	network6 = soap_client.service.getIPRangedByIP(configID, "IP6Network",IP6)
	return network6

def GetNetworksV6(soap_client,network,start,count):
	ipv6Networks = soap_client.service.searchByObjectTypes(network,"IP6Network",start,count)
	return ipv6Networks[0]

def GetBlockV6(soap_client,configID,IP6):
   block6 = soap_client.service.getIPRangedByIP(configID, "IP6Block",IP6)
   return block6

def GetBlocksV6(soap_client,block,start,count):
	ipv6Blocks = soap_client.service.searchByObjectTypes(block,"IP6Block",start,count)
	return ipv6Blocks[0]

def GetNetworksV4(soap_client,network,start,count):
	ipv4Networks = soap_client.service.searchByObjectTypes(network,"IP4Network",start,count)
	return ipv4Networks[0]

def GetBlockV4byIP(soap_client,configID,IP4):
   block4 = soap_client.service.getIPRangedByIP(configID, "IP4Block",IP4)
   return block4

def GetNetworkV4byIP(soap_client,configID,IP4):
   net4 = soap_client.service.getIPRangedByIP(configID, "IP4Network",IP4)
   return net4

def AddBlockV4(soap_client,parentID,CIDR,props):
	blockv4 = soap_client.service.addIP4BlockByCIDR(parentID,CIDR,props)
	return blockv4

def GetBlockV4(soap_client,parentID,CIDR):
	props = ""
	blockv4 = soap_client.service.getEntityByCIDR(parentID,CIDR,"IP4Block")
	if blockv4['id'] == 0:
		return
	return blockv4

def AddNetworkV4(soap_client,parentID,CIDR,props):
	blockv4 = soap_client.service.addIP4Network(parentID,CIDR,props)
	return blockv4

def GetNetworkV4(soap_client,parentID,CIDR):
	props = ""
	blockv4 = soap_client.service.getEntityByCIDR(parentID,CIDR,"IP4Network")
	if blockv4['id'] == 0:
		return
	return blockv4

def GetBlocksV4(soap_client,block,start,count):
	ipv4Blocks = soap_client.service.searchByObjectTypes(block,"IP4Block",start,count)
	if blockv4['id'] == 0:
		return
	return ipv4Blocks[0]

# Get BAM information
def GetBAMInfo(soap_client):
   info = soap_client.service.getSystemInfo()
   return info

# Device Functions
def GetDevice(soap_client,configID,device):
	Device = soap_client.service.getEntityByName(configID,device,"Device")
	if Device['id'] == 0:
		return
	return Device

def DelDevice(soap_client,configID,device):
	Device = soap_client.service.getEntityById(device)
	soap_client.service.delete(Device['id'])
	return


def GetDeviceTypes(soap_client,device,start,count):
	DeviceTypes = soap_client.service.searchByObjectTypes(device,"DeviceType",start,count)
	if DeviceTypes:
		return DeviceTypes[0]
	return

def GetDeviceSubTypes(soap_client,device,start,count):
	DeviceSubTypes = soap_client.service.searchByObjectTypes(device,"DeviceSubtype",start,count)
	if DeviceSubTypes:
		return DeviceSubTypes[0]
	return

def GetAWSDeviceTypeID(soap_client):
   AWSDeviceTypeID = soap_client.service.getEntityByName(0, "Amazon Web Services", 'DeviceType')['id']
   return AWSDeviceTypeID

def GetAzureDeviceTypeID(soap_client):
   AzureDeviceTypeID = soap_client.service.getEntityByName(0, "Microsoft Azure", 'DeviceType')['id']
   return AzureDeviceTypeID

def GetGCPDeviceTypeID(soap_client):
   GCPDeviceTypeID = soap_client.service.getEntityByName(0, "Google Cloud Platform", 'DeviceType')['id']
   return GCPDeviceTypeID

def AddDeviceType(soap_client,DeviceTypeName,props):
	AddDeviceType = soap_client.service.addDeviceType(DeviceTypeName,props)
	return AddDeviceType

def AddDeviceSubType(soap_client,parentID,DeviceSubTypeName,props):
	AddDeviceSubType = soap_client.service.addDeviceSubtype(parentID,DeviceSubTypeName,props)
	return AddDeviceSubType

def AssignIP4Address(soap_client, parentID, ipv4, macaddr):
   AssignIP4Address = soap_client.service.assignIP4Address(parentID,ipv4,macaddr,'','MAKE_STATIC','')
   return AssignIP4Address

#UDF functions
def GetUDFs(soap_client,object_type):
	UDFs = soap_client.service.getUserDefinedFields(object_type,False)
	return UDFs[0]

#TAG functions
def GetTAG_Group(soap_client,taggroup):
   TagGroups = soap_client.service.getEntityByName(0, taggroup, 'TagGroup')
   return TagGroups[0]

#TAG functions
def GetTAGs(soap_client,tag_group):
   Tag = soap_client.service.getEntities(tag_group, "Tag", 0,1000)
   return Tag

def GetTAG(soap_client,taggroup,tagname):
   Tag = soap_client.service.getEntityByName(taggroup, tagname, 'Tag')
   return Tag

#TAG functions
def AddTAG(soap_client,tag_group,tagname):
   props = ""
   Tag = soap_client.service.addTag(tag_group, tagname, props)
   return Tag

#Add a Configuration
def AddAWSConfiguration(soap_client,name,version):
   configuration = soap_client.factory.create('APIEntity')
   configuration.id=""
   configuration.name=name
   configuration.type="Configuration"
   if version == "9.0.0-314.GA.bcn":
      configuration.properties=""
   else:
      configuration.properties="configurationGroup=Amazon Web Services" + '|' + 'description=Automatically generated by AWS CloudAtlas'
   Conf = soap_client.service.addEntity(0,configuration)
   return Conf

def AddAzureConfiguration(soap_client,name):
   configuration = soap_client.factory.create('APIEntity')
   configuration.id=""
   configuration.name=name
   configuration.type="Configuration"
   configuration.properties="configurationGroup=Microsoft Azure" + '|' + 'description=Automatically generated by Azure CloudAtlas'
   Conf = soap_client.service.addEntity(0,configuration)
   return Conf

def AddGCPConfiguration(soap_client,name):
   configuration = soap_client.factory.create('APIEntity')
   configuration.id=""
   configuration.name=name
   configuration.type="Configuration"
   configuration.properties="configurationGroup=Google Cloud Platform" + '|' + 'description=Automatically generated by GCP CloudAtlas'
   Conf = soap_client.service.addEntity(0,configuration)
   return Conf

#Get a Configuration
def GetConfiguration(soap_client,conf):
	Conf = soap_client.service.getEntityByName(0,conf,"Configuration")
	if Conf['id'] == 0:
		return
	return Conf

def GetConfigurationbyID(soap_client,ID):
	Conf = soap_client.service.getEntityById(ID)
	if Conf['id'] == 0:
		return
	return Conf

#Link Entities
def linkEntities(soap_client,link1,link2):
	props = ""
	link = soap_client.service.linkEntities(link1,link2,props)
	return link

# View Functions
def get_bam_viewid(soap_client, configId, viewName):
   view = soap_client.service.getEntityByName(configId, viewName, 'View')
   viewId = long(view['id'])
   #print ("BCN: Got View ID %d" % (viewId))
   return viewId

if __name__ == '__main__':
    main()
