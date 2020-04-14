"""
 GuardDuty Helper
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json, boto3, os, logging, account_session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def getClient(findingArn: str):
    FindingId=findingArn.split("/")[3]
    DetectorId=findingArn.split("/")[1]
    targetAccount=findingArn.split("/")[0].split(":")[4]

    session=account_session.get_session(targetAccount, os.environ['TargetAccountSecurityRoleName']) 
    client = session.client('guardduty')
    return(client, DetectorId, FindingId) 

def getGuardDutyFinding(findingArn: str):
    (client, DetectorId, FindingId) = getClient(findingArn) 
    response = client.get_findings(
        DetectorId=DetectorId,
        FindingIds=[
            FindingId,
        ])
    return response['Findings'][0]

def archiveGuardDutyFinding(findingArn: str):
    (client, DetectorId, FindingId) = getClient(findingArn) 
    response = client.archive_findings(
        DetectorId=DetectorId,
        FindingIds=[
            FindingId,
        ])

