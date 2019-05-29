#!/usr/bin/env python3
# Author: Brian Shorland - BlueCat Networks

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient

import bamclient as BAM
soap_client = BAM.bam_login()
props = ""
if BAM.GetAzureDeviceTypeID(soap_client) == False:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Adding Azure DeviceTypes to BlueCat Address Manager ' + BAM.bcolours.ENDC )
	AzureDevType = BAM.AddDeviceType(soap_client,"Microsoft Azure",props)
	AzureInsanceSubType = BAM.AddDeviceSubType(soap_client,AzureDevType,"Azure Virtual Machine",props)
else:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Azure DeviceTypes already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	x = BAM.GetAzureDeviceTypeID(soap_client)
	AzureDevType = x
	AzureInsanceSubType = soap_client.service.getEntityByName(x, "Azure Virtual Machine", 'DeviceSubtype')['id']
print("")

azure_subscription = ""
azure_client = ""
azure_client_secret = ""
azure_tenent_id = ""

GROUP_NAME = 'myResourceGroup'

subscription_id = azure_subscription

print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] subscription_id: ' + subscription_id + BAM.bcolours.ENDC )
print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] azure_client: ' + azure_client + BAM.bcolours.ENDC )
print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] azure_tenent_id: ' + azure_tenent_id + BAM.bcolours.ENDC )
print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Resource Group: ' + GROUP_NAME + BAM.bcolours.ENDC )
print("\n")

# Get all VNETS in Subscription, change to list(GROUP_NAME) for VNETs in resource group
def get_azure_infra():
    print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] get_azure_infra()' + BAM.bcolours.ENDC )
    vnets = network_client.virtual_networks.list_all()
    for net in vnets:
        # print(net)
        print("\tAzure VNETs: {}".format(net.name))
        print("\tAzure VNETs Location: {}".format(net.location))
        address_space = str(net.address_space.address_prefixes).split("'")[1].strip()
        print("\tAzure VNETs Address Space: {}".format(address_space))
        subs = network_client.subnets.list(GROUP_NAME,net.name)
        for s in subs:
           print("\tPrivate Subnet CIDR: {}".format(s.address_prefix))
           print("\tPrivate Subnet Name: {}".format(s.name))
        print("\n")

# Get all VMs in Subscription, change to list(GROUP_NAME) for VMs in resource group only
def get_azure_vms():
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] get_azure_vms()' + BAM.bcolours.ENDC )
	for vm in compute_client.virtual_machines.list_all():
		vmd = compute_client.virtual_machines.get(GROUP_NAME, vm.name, expand='instanceView')
		hardware = vmd.hardware_profile
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Virtual Machine Discovered' + BAM.bcolours.ENDC )
		for stat in vmd.instance_view.statuses:
			cur_status = stat.display_status
		for interface in vm.network_profile.network_interfaces:
			name=" ".join(interface.id.split('/')[-1:])
			sub="".join(interface.id.split('/')[4])
			ipconfs=network_client.network_interfaces.get(sub, name).ip_configurations
			for i in ipconfs:
				vnet="".join(i.subnet.id.split('/')[-3])
				b = network_client.virtual_networks.get(GROUP_NAME,vnet)
				vnet_name = b.name
				address_space = str(b.address_space.address_prefixes).split("'")[1].strip()
				sn="".join(i.subnet.id.split('/')[-1:])
				sub = network_client.subnets.get(GROUP_NAME,vnet,sn)
				public_ip = network_client.public_ip_addresses.get(GROUP_NAME,vm.name + "-ip")
				if public_ip.dns_settings is None:
					pubdns = "NA"
				else:
					pubdns = public_ip.dns_settings.fqdn

		config = GROUP_NAME + " [" +  vnet + "]"

		# Check if VNET configuration in BAM already is present, if not add the VNET configuration
		conf = BAM.GetConfiguration(soap_client,config)
		if conf:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] VNET Configuration already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
		else:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] VNET Configuration not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
			conf = vnet
			BAM.AddAzureConfiguration(soap_client,config)

		# Check if Network Block of VPC is already in the config in BAM, if not add the required Block
		conf = BAM.GetConfiguration(soap_client,config)
		blk = BAM.GetBlockV4(soap_client,conf.id,str(address_space))
		if blk:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] VNET Network Block already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
		else:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Adding VNET Network Block to BlueCat Address Manager ' + BAM.bcolours.ENDC )
			conf = BAM.GetConfiguration(soap_client,config)
			pid = str(conf['id'])
			props="name=" + vnet_name
			blk = BAM.AddBlockV4(soap_client,pid,address_space,props)

		# Check if Subnet of VNET is already in the Block in BAM, if not add the required Subnet
		blk = BAM.GetBlockV4(soap_client,conf.id,str(address_space))
		subn = BAM.GetNetworkV4(soap_client,blk.id,str(sub.address_prefix))
		if subn:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] VNET Subnet already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
		else:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Adding VNET Subnet to BlueCat Address Manager ' + BAM.bcolours.ENDC )
			props="name=" + sn
			BAM.AddNetworkV4(soap_client,blk.id,str(sub.address_prefix),props)

		# Check if Instance Device is already added, if not add the required device
		dev = BAM.GetDevice(soap_client,conf.id,vm.name)
		if dev:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Azure VM Device in BlueCat Address Manager, updating  ' + BAM.bcolours.ENDC )
			BAM.DelDevice(soap_client,conf.id,dev.id)
			props="PrivateDNSName=Not Applicable" + '|' + "PublicDNSName=" + pubdns + '|' + "InstanceState="+cur_status + '|' + "InstanceType="+hardware.vm_size + "|" + "AvailabilityZone=" + vm.location + "|" + "IPv4PublicIP=" + str(public_ip.ip_address)
			device = soap_client.service.addDevice(str(conf['id']),vm.name,AzureDevType,AzureInsanceSubType,i.private_ip_address,"",props)

		else:
			print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Azure CloudAtlas] Azure VM Device not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
			props="PrivateDNSName=Not Applicable" + '|' + "PublicDNSName=" + pubdns + '|' + "InstanceState="+cur_status + '|' + "InstanceType="+hardware.vm_size + "|" + "AvailabilityZone=" + vm.location + "|" + "IPv4PublicIP=" + str(public_ip.ip_address)
			device = soap_client.service.addDevice(str(conf['id']),vm.name,AzureDevType,AzureInsanceSubType,i.private_ip_address,"",props)

		print("")


def get_credentials():
	credentials = ServicePrincipalCredentials(
		client_id = azure_client,
		secret = azure_client_secret,
		tenant = azure_tenent_id
	)
	return credentials

credentials = get_credentials()
network_client = NetworkManagementClient(credentials, subscription_id)
compute_client = ComputeManagementClient(credentials, subscription_id)

get_azure_infra()
get_azure_vms()
