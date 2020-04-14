"""
 Checks for security exception in tags
 and decativated the user/role by attaching deny all policy
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json, boto3, os, security_hub, notify, logging, account_session, guard_duty

logger = logging.getLogger()
logger.setLevel(logging.INFO)
    
def lambda_handler(event, context):
    
    SecurityTagKey=os.environ['SecurityTagKey']
    TargetAccountSecurityRoleName=os.environ['TargetAccountSecurityRoleName'] 
    BlockPolicyArn=os.environ['BlockPolicyArn'] 

    if event['detail-type'] == "GuardDuty Finding":
        finding=event["detail"]
    elif event['detail-type'] == "Security Hub Findings - Custom Action":
        finding=security_hub.getFinding(event)
        
    else:
        raise Exception("Neither GuardDuty nor SecurityHub event")

    event_id=finding['id']
    targetAccount=finding["accountId"]
    principle_id = finding["resource"]["accessKeyDetails"]["userName"]
    principle_type = finding["resource"]["accessKeyDetails"]["userType"]
    
    session=account_session.get_session(targetAccount, os.environ['TargetAccountSecurityRoleName']) 

    logger.info(f"GuardDuty Duty event {event_id} triggers checking principle {principle_type} of type {principle_type} in account {targetAccount}")
    client = session.client('iam')
    
    if principle_type=="AssumedRole":
        response = client.get_role(RoleName=principle_id)
        
        if 'Tags' in response['Role']:
            for t in response['Role']['Tags']:
                if t['Key'] == SecurityTagKey:
                    logger.info(f"Security exception defined with tag {SecurityTagKey}. Skipping blocking {principle_id} of type {principle_type} in account {targetAccount}")
                    return

        client.attach_role_policy (RoleName=principle_id, PolicyArn=BlockPolicyArn)
    else:
        response = client.get_user(UserName=principle_id)
        
        if 'Tags' in response['User']:
            for t in response['User']['Tags']:
                if t['Key'] == SecurityTagKey:
                    logger.info(f"Security exception defined with tag {SecurityTagKey}. Skipping blocking {principle_id} of type {principle_type} in account {targetAccount}")
                    return
        client.attach_user_policy (UserName=principle_id, PolicyArn=BlockPolicyArn)
    
    guard_duty.archiveGuardDutyFinding(finding["arn"])

    notify.sendNotification(f"Attached deny policy to principle {principle_id} of type {principle_type} in account {targetAccount}. Guard Duty finding id {event_id} archived.")

