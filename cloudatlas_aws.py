#!/usr/bin/env python3
# Author: Brian Shorland - BlueCat Networks

import boto3
import bamclient as BAM

region_name = ""
aws_access_key_id = ""
aws_secret_access_key = ""

soap_client = BAM.bam_login()


# Get BAM version

x = BAM.GetBAMInfo(soap_client)
version = BAM.getPropsField(x, "version")


# Check if UDFs in BAM exists

CheckUDFs = BAM.GetUDFs(soap_client,"Device")

CheckUDFs_count = 0
for udf in CheckUDFs:
	if (udf[1] == "InstanceType"
	or udf[1] == "InstanceState"
	or udf[1] == "PublicDNSName"
	or udf[1] == "PrivateDNSName"
	or udf[1] == "IPv4PublicIP"
	or udf[1] == "AvailabilityZone"): CheckUDFs_count = CheckUDFs_count + 1

# If one of UDFs not exists, exit

if CheckUDFs_count < 6:
	print("Exit. Please check your UDFs configured on BAM")
	exit()

props = ""
if BAM.GetAWSDeviceTypeID(soap_client) == False:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] Adding AWS DeviceTypes to BlueCat Address Manager ' + BAM.bcolours.ENDC )
	AWSDevType = BAM.AddDeviceType(soap_client,"Amazon Web Services",props)
	AWSInsanceSubType = BAM.AddDeviceSubType(soap_client,AWSDevType,"AWS EC2 Instance",props)
else:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] AWS DeviceTypes already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	x = BAM.GetAWSDeviceTypeID(soap_client)
	AWSDevType = x
	AWSInsanceSubType = soap_client.service.getEntityByName(x, "AWS EC2 Instance", 'DeviceSubtype')['id']

print("")

print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] AWS Region: ' + region_name + BAM.bcolours.ENDC )
print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] AWS Access Key: ' + aws_access_key_id + BAM.bcolours.ENDC )
print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] AWS Secret Access Key: ' + aws_secret_access_key + BAM.bcolours.ENDC )

ec2 = boto3.resource('ec2',region_name=region_name,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)

for instance in ec2.instances.all():
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] EC2 Instance Found: ' + instance.id + BAM.bcolours.ENDC )
	if instance.subnet_id:
		subnet = ec2.Subnet(instance.subnet_id)
	if instance.vpc_id:
		vpc = ec2.Vpc(instance.vpc_id)
		if vpc.dhcp_options:
			dhcp_options = ec2.DhcpOptions(vpc.dhcp_options.id)
	if instance.network_interfaces:
		for iface in instance.network_interfaces: mac_addr = iface.mac_address
	
	print("")

	conf = instance.vpc_id

	# Check if VPC configuration in BAM already is present, if not add the VPC configuration
	conf = BAM.GetConfiguration(soap_client,instance.vpc_id)
	if conf:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] VPC Configuration already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	else:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] VPC Configuration not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
		conf = instance.vpc_id
		BAM.AddAWSConfiguration(soap_client,conf, version)

	# Check if Network Block of VPC is already in the config in BAM, if not add the required Block
	conf = BAM.GetConfiguration(soap_client,instance.vpc_id)

	blk = BAM.GetBlockV4(soap_client,conf.id,str(vpc.cidr_block))
	if blk:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] VPC Network Block already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	else:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] Adding VPC Network Block to BlueCat Address Manager ' + BAM.bcolours.ENDC )
		conf = BAM.GetConfiguration(soap_client,instance.vpc_id)
		pid = str(conf['id'])
		props="name=" + instance.vpc_id
		blk = BAM.AddBlockV4(soap_client,pid,vpc.cidr_block,props)

	# Check if Subnet of VPC is already in the Block in BAM, if not add the required Subnet

	blk = BAM.GetBlockV4(soap_client,conf.id,str(vpc.cidr_block))
	sub = BAM.GetNetworkV4(soap_client,blk.id,str(subnet.cidr_block))
	if sub:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] VPC Subnet already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	else:
		blk = BAM.GetBlockV4(soap_client,conf.id,str(vpc.cidr_block))
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] Adding VPC Subnet to BlueCat Address Manager ' + BAM.bcolours.ENDC )
		props="name=" + instance.subnet_id
		BAM.AddNetworkV4(soap_client,blk.id,subnet.cidr_block,props)

	# Check if Instance Device is already added, if not add the required device
	dev = BAM.GetDevice(soap_client,conf.id,instance.id)
	if dev:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] EC2 Instance Device in BlueCat Address Manager, updating  ' + BAM.bcolours.ENDC )
		BAM.DelDevice(soap_client,conf.id,dev.id)
		props="PrivateDNSName="+instance.private_dns_name + '|' + "PublicDNSName=" + instance.public_dns_name + '|' + "InstanceState="+instance.state['Name'] + '|' + "InstanceType="+instance.instance_type + "|" + "AvailabilityZone=" + instance.placement['AvailabilityZone'] + "|" + "IPv4PublicIP=" + str(instance.public_ip_address)
		device = soap_client.service.addDevice(str(conf['id']),instance.id,AWSDevType,AWSInsanceSubType,instance.private_ip_address,"",props)
	#	device = BAM.AssignIP4Address(soap_client,str(conf['id']),instance.private_ip_address, mac_addr)

	else:
		print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[AWS CloudAtlas] EC2 Instance Device not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
		props="PrivateDNSName="+instance.private_dns_name + '|' + "PublicDNSName=" + instance.public_dns_name + '|' + "InstanceState="+instance.state['Name'] + '|' + "InstanceType="+instance.instance_type + "|" + "AvailabilityZone=" + instance.placement['AvailabilityZone'] + "|" + "IPv4PublicIP=" + str(instance.public_ip_address)
		device = soap_client.service.addDevice(str(conf['id']),instance.id,AWSDevType,AWSInsanceSubType,instance.private_ip_address,"",props)
	#	device = BAM.AssignIP4Address(soap_client,str(conf['id']),instance.private_ip_address, mac_addr)


	print("")
