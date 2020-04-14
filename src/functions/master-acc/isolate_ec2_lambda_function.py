"""
 Isolates an EC2 instance by attaching an empty security groups. If security exception in tags is defined that it is skipped
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json, boto3, os, security_hub, notify, logging, account_session, guard_duty

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    SecurityTagKey=os.environ['SecurityTagKey']
    TargetAccountSecurityRoleName=os.environ['TargetAccountSecurityRoleName'] 

    if event['detail-type'] == "GuardDuty Finding":
        finding=event["detail"]
    elif event['detail-type'] == "Security Hub Findings - Custom Action":
        finding=security_hub.getFinding(event)
        
    else:
        raise Exception("Neither GuardDuty nor SecurityHub event")
    
    i_id = finding["resource"]["instanceDetails"]["instanceId"]
    targetAccount=finding["accountId"]
    event_id=finding['id']
    
    logger.info(f"GuardDuty Duty event {event_id} triggers checking instance {i_id} in account {targetAccount}")
     
    session=account_session.get_session(targetAccount, os.environ['TargetAccountSecurityRoleName']) 
    
    client = session.client('ec2')
    ec2 = client.describe_instances(InstanceIds=[i_id])
    if "Tags" in ec2['Reservations'][0]['Instances'][0]:
        for t in ec2['Reservations'][0]['Instances'][0]["Tags"]:
            if t['Key'] == SecurityTagKey:
                logger.info(f"Security exception defined with tag {SecurityTagKey}. Skipping Isolation of instance {i_id} in account {targetAccount}")
                return

    secGrName=f"secIsolation-{event_id}"
    vpcID=ec2['Reservations'][0]['Instances'][0]["VpcId"]
    # Check if isolation security group already exists 
    try:
        r=client.describe_security_groups(
             Filters=[ 
                { 'Name': 'group-name', 'Values': [ secGrName ] },
                { 'Name': 'vpc-id', 'Values': [ vpcID ] } ] )
        secGrId=r['SecurityGroups'][0]['GroupId']
        logger.info(f'Found existing isolation Sec Group {secGrId}')
    except:            
        r = client.create_security_group( Description='security isolation', GroupName=secGrName, VpcId=vpcID)
        secGrId=r['GroupId']
        client.revoke_security_group_egress(IpPermissions= [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}], "Ipv6Ranges": [], "PrefixListIds": [], "UserIdGroupPairs": []}], GroupId=secGrId)
        logger.info(f'Created new isolation Sec Group {secGrId}')


    for eni in ec2['Reservations'][0]['Instances'][0]['NetworkInterfaces']:
        client.modify_network_interface_attribute (  NetworkInterfaceId=eni["NetworkInterfaceId"], Groups=[secGrId] )
    
    guard_duty.archiveGuardDutyFinding(finding["arn"])
    
    notify.sendNotification(f"Isolation security group {secGrId} created and attached to instance {i_id} in account {targetAccount}. Guard Duty finding id {event_id} archived")

    
