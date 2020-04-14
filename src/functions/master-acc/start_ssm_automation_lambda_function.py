"""
 Excutes ssm automaton document if security 
  exception in tags is not defined 
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""
import json, boto3, os, notify, logging, account_session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
   
    logger.info(f"recieved event: {json.dumps(event)}")

    SecurityTagKey=os.environ['SecurityTagKey']
    region=os.environ['AWS_REGION']
    targetAccount=event["account"]
    
    session=account_session.get_session(targetAccount, os.environ['TargetAccountSecurityRoleName']) 

    # check for security exeption 
    client = session.client('resourcegroupstaggingapi')
    paginator = client.get_paginator('get_resources')
    pages = paginator.paginate(
        TagFilters=[
            { 'Key': SecurityTagKey, } ],
        ResourceTypeFilters=[event["resourseType"]])

    for page in pages:
        for res in page['ResourceTagMappingList']:
            if event["resourceId"] in res['ResourceARN']:
                logger.info(f"Security exception defined with tag {SecurityTagKey}. Skipping {event['resourceId']} of type {event['resourseType']}") 
                return

    # execute automation 
    if "AutomationDocumentName" in event:
        client = boto3.client('ssm')
        response = client.start_automation_execution(
            DocumentName=event['AutomationDocumentName'],
            Parameters=event['AutomationParameters'],
            TargetLocations=[ { "Accounts": [targetAccount], "Regions" : [region]} ])
            
        notify.sendNotification(f"Triggered incident response in account {event['account']}, SSM document {event['AutomationDocumentName']} with id {response['AutomationExecutionId']} and input parameters " + json.dumps(event['AutomationParameters']) )    
            
  

