"""
 Checks for security exception in tags
 and confines a Security Group 
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""
import json, boto3, os, notify, account_session, logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    AllowedNetworkRangeIPv4=os.environ['AllowedNetworkRangeIPv4']
    AllowedNetworkRangeIPv6=os.environ['AllowedNetworkRangeIPv6']
    SecurityTagKey=os.environ['SecurityTagKey']

    if event['source'] == "aws.config":
             sg_id=event["detail"]["resourceId"]
             targetAccount=event["account"]
    else: 
        raise Exception('Unknown event source. Supported only aws.config')
    
    session=account_session.get_session(targetAccount, os.environ['TargetAccountSecurityRoleName']) 
    
    logger.info(f"Checking security group {sg_id} in account {targetAccount}")
    client = session.client('ec2')
    response = client.describe_security_groups(GroupIds=[ sg_id ])
    
    if "Tags" in response['SecurityGroups'][0]:    
         for t in response['SecurityGroups'][0]['Tags']:
             if t['Key'] == SecurityTagKey:
                 logger.info(f"Security exception defined with tag {SecurityTagKey}. Skipping security group {sg_id} to confine") 
                 return
    
    for p in response['SecurityGroups'][0]['IpPermissions']:
        for r in p['IpRanges']:
            if r["CidrIp"] == "0.0.0.0/0":
                client.revoke_security_group_ingress(IpPermissions=[p], GroupId=sg_id)
                r["CidrIp"]=AllowedNetworkRangeIPv4
                client.authorize_security_group_ingress(IpPermissions=[p], GroupId=sg_id)
        for r in p['Ipv6Ranges']:
            if r["CidrIpv6"] == "::/0":
                client.revoke_security_group_ingress(IpPermissions=[p], GroupId=sg_id)
                r["CidrIpv6"]=AllowedNetworkRangeIPv6
                client.authorize_security_group_ingress(IpPermissions=[p], GroupId=sg_id)
    
    notify.sendNotification(f"Confined security group {sg_id} in account id {targetAccount} to safe CIDR")
