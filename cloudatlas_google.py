#!/usr/bin/env python3
# Author: Brian Shorland - BlueCat Networks

import bamclient as BAM



soap_client = BAM.bam_login()
props = ""
if BAM.GetGCPDeviceTypeID(soap_client) == False:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Adding Google Compute Platform DeviceTypes to BlueCat Address Manager ' + BAM.bcolours.ENDC )
	GCPDevType = BAM.AddDeviceType(soap_client,"Google Cloud Platform",props)
	GCPInstanceSubType = BAM.AddDeviceSubType(soap_client,GCPDevType,"Google Compute Engine",props)
else:
	print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Google Compute Platform DeviceTypes already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
	x = BAM.GetGCPDeviceTypeID(soap_client)
	GCPDevType = x
	GCPInstanceSubType = soap_client.service.getEntityByName(x, "Google Compute Engine", 'DeviceSubtype')['id']
print("")


print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Alpha Code ' + BAM.bcolours.ENDC )


import googleapiclient.discovery
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file("My First Project-1796c6836405.json")
service = discovery.build('compute', 'v1', credentials=credentials)

# Get the ProjectID from the Name, uses CRM
crm = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
filter = "name=\"My First Project\""
project = crm.projects().list(filter=filter).execute()
a, *rest = project['projects']
print("GCP Project Name:",a['name'])
print("GCP ProjectID:",a['projectId'])
print("")
PROJECT_ID = str(a['projectId'])
PROJECT_NAME = str(a['name'])

def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def checkInstancesInZone(ZONE):
	compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
	instances = list_instances(compute, PROJECT_ID, ZONE)

	if (instances != None):
		for instance in instances:
			print('Instance name: ' + instance['name'] + "\nInstance ID: "  + instance['id']  + '\nZone: ' + ZONE + '\nState: ' + instance['status'])
			machine_type = "".join(str(instance['machineType']).split('/')[-1:])
			print('Machine Type:',machine_type)
			network_priv = instance['networkInterfaces']
			for x in network_priv:
				print("Private IP",x['networkIP'])

				# Get subnet details, CIDR and GW
				subnetwork = "".join(str(x['subnetwork']).split('/')[-1:])
				sregion = "".join(str(x['subnetwork']).split('/')[-3])
				request = service.subnetworks().get(project=PROJECT_ID, region=sregion, subnetwork=subnetwork)
				response = request.execute()
				print("Private Subnet CIDR:",response['ipCidrRange'])
				print("Private Subnet Gateway:",response['gatewayAddress'])
				if 'hostname' in instance:
					print("Custom FQDN:",instance['hostname'])
					hostname = instance['hostname']
				else:
					hostname = ""
				internal_dns = instance['name']+"."+ZONE+".c." + PROJECT_ID + ".internal"
				print("Internal (Zonal) DNS Name:",internal_dns)
				a, *rest = x['accessConfigs']
				if 'natIP' in a:
					print ("Public IP:",a['natIP'])
					public_ip = a['natIP']
				else:
					public_ip = ""


			config = PROJECT_NAME + " [" +  ZONE + "]"
			# Check if Project/Region configuration in BAM already is present, if not add the Project/Region configuration
			conf = BAM.GetConfiguration(soap_client,config)
			if conf:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Project/Region Configuration already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
			else:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Project/Region Configuration not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
				BAM.AddGCPConfiguration(soap_client,config)

			# Check if Network Block of VPC is already in the config in BAM, if not add the required Block
			conf = BAM.GetConfiguration(soap_client,config)
			blk = BAM.GetBlockV4(soap_client,conf.id,response['ipCidrRange'])
			if blk:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Project/Region Block already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
			else:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Adding Project/Region Network Block to BlueCat Address Manager ' + BAM.bcolours.ENDC )
				conf = BAM.GetConfiguration(soap_client,config)
				pid = str(conf['id'])
				props="name=" + response['ipCidrRange']
				blk = BAM.AddBlockV4(soap_client,pid,response['ipCidrRange'],props)

			# Check if Subnet of VNET is already in the Block in BAM, if not add the required Subnet
			blk = BAM.GetBlockV4(soap_client,conf.id,response['ipCidrRange'])
			subn = BAM.GetNetworkV4(soap_client,blk.id,response['ipCidrRange'])
			if subn:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Project/Region Subnet already in BlueCat Address Manager ' + BAM.bcolours.ENDC )
			else:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Adding Project/Region Subnet to BlueCat Address Manager ' + BAM.bcolours.ENDC )
				props="name=" + response['ipCidrRange']
				BAM.AddNetworkV4(soap_client,blk.id,str(response['ipCidrRange']),props)

			# Check if Instance Device is already added, if not add the required device
			dev = BAM.GetDevice(soap_client,conf.id,instance['name'])
			if dev:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Google VM Device in BlueCat Address Manager, updating  ' + BAM.bcolours.ENDC )
				BAM.DelDevice(soap_client,conf.id,dev.id)
				props="PrivateDNSName=" + internal_dns+ '|' + "PublicDNSName=" + hostname + '|' + "InstanceState="+instance['status'] + '|' + "InstanceType="+machine_type + "|" + "AvailabilityZone=" + ZONE + "|" + "IPv4PublicIP=" + public_ip
				device = soap_client.service.addDevice(str(conf['id']),instance['name'],GCPDevType,GCPInstanceSubType,x['networkIP'],"",props)

			else:
				print (BAM.bcolours.GREEN + BAM.bcolours.BOLD + '[Google CloudAtlas] Google VM Device not found, adding to BlueCat Address Manager ' + BAM.bcolours.ENDC )
				props="PrivateDNSName=" + internal_dns+ '|' + "PublicDNSName=" + hostname + '|' + "InstanceState="+instance['status'] + '|' + "InstanceType="+machine_type + "|" + "AvailabilityZone=" + ZONE + "|" + "IPv4PublicIP=" + public_ip
				device = soap_client.service.addDevice(str(conf['id']),instance['name'],GCPDevType,GCPInstanceSubType,x['networkIP'],"",props)
			print("\n")

def main():
	# Given a ProjectID search through all the service zones for instances
    request = service.zones().list(project=PROJECT_ID)
    while request is not None:
        response = request.execute()
        for zone in response['items']:
            checkInstancesInZone(zone['description'])
        request = service.zones().list_next(previous_request=request, previous_response=response)

main()
