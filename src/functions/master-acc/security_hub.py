"""
 Functions for security hub custom action handling
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json, boto3, os, logging, account_session, guard_duty

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Convert to lower case the first letter of dict key 
def convert(d: dict):
    new = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = convert(v)
        n=k[:1].lower() + k[1:] 
        new[n] = v
    return new

def getFinding(event: dict):
    if len(event['detail']['findings'])>1:
        raise Exception("Multiple findins not supported") 
    if len(event['detail']['findings'][0]['Resources']) > 1:
         raise Exception("Multiple resources in one finding not supported") 
    if event['detail']['findings'][0]['Resources'][0]['Type'] not in [ "AwsEc2Instance", "AwsIamAccessKey"]: 
         raise Exception("Only Resources Type AwsEc2Instance or AwsIamAccessKey are supprted ") 
    if "guardduty" not in event['detail']['findings'][0]['ProductArn']:
         raise Exception("Only GuardDuty Events in Securtity Hub are supprted") 
     
    finding=guard_duty.getGuardDutyFinding(event["detail"]["findings"][0]["Id"])
    # Convert to lower letter the keys of dict 
    finding=convert(finding) 

    logger.info(f'Securiy Hub event {event["id"]} based on GuardDuty') 

    return finding
