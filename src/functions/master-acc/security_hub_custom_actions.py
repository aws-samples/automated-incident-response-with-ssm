"""
 Creates cusom action in Security Hub and CloudWatch Rules 
 Custom Resource Cloud Formation 

 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json
import logging
import uuid
import threading
import sys,os
import boto3  
import cfnresponse
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def timeout(event, context):
    logger.error('Execution is about to time out, sending failure response to CloudFormation')
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)

def lambda_handler(event, context):
    # make sure we send a failure to CloudFormation if the function is going to timeout
    timer = threading.Timer((context.get_remaining_time_in_millis() / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()
    logger.info ('Received event: %s' % json.dumps(event))
    status = cfnresponse.SUCCESS
    try:
        CustomActions = event['ResourceProperties']['CustomActions']
        AccountId = event['ResourceProperties']['AccountId']
        
        client = boto3.client('securityhub')
        response = client.describe_hub() # exits if security hub not enabled
        lmb = boto3.client('lambda')
        conf = boto3.client('config')
        events = boto3.client('events')

        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
                logger.info("create")
                for action in CustomActions:
                  try:
                    logger.info(f"working on {action['Name']}")
                    response = client.create_action_target( Name=action['Name'], Description=action['Description'], Id=action['ActionId']+"SH")
                    rule = events.put_rule( Name=action['ActionId']+"-SecurityHub", 
                                                EventPattern='{ "source": [ "aws.securityhub" ], "detail-type": [ "Security Hub Findings - Custom Action" ], "detail": { "actionName": [ "' + action['Name'] + '" ] }}' ,
                                                Description=action['Description'])

                    response = events.put_targets( Rule=action['ActionId']+"-SecurityHub", Targets=[ { 'Id': action['ActionId']+"-SecurityHub" , 'Arn': action['Target']  } ] )
                    if "arn:aws:lambda" in action['Target']:
                      response = lmb.add_permission( FunctionName=action['Target'] , StatementId=action['ActionId']+"-SecurityHub", Action='lambda:InvokeFunction', Principal='events.amazonaws.com', SourceArn=rule['RuleArn'] )
                  except Exception as e:
                    logger.error('Exception: %s' % e, exc_info=True)
        # delete event    
        elif event['RequestType'] == 'Delete':
                logger.info("delete")
                region=os.environ['AWS_REGION']
                for action in CustomActions:
                  try:
                    logger.info(f"working on {action['Name']}")
                    n=action['ActionId']+"SH"
                    response = client.delete_action_target( ActionTargetArn=f"arn:aws:securityhub:{region}:{AccountId}:action/custom/{n}")
                    response = events.remove_targets( Rule=action['ActionId']+"-SecurityHub", Ids=[  action['ActionId']+"-SecurityHub" ] )
                    response = events.delete_rule( Name=action['ActionId']+"-SecurityHub")
                    if "arn:aws:lambda" in action['Target']:
                      response = lmb.remove_permission( FunctionName=action['Target'], StatementId=action['ActionId']+"-SecurityHub")
                  except Exception as e:
                    logger.error('Exception: %s' % e, exc_info=True)
                      
        else:
          logger.warning('Received unknown cloud formation event')

    except Exception as e:
        logger.error('Exception: %s' % e, exc_info=True)
        if "DescribeHub" not in str(e): 
            status = cfnresponse.FAILED
    finally:
        timer.cancel()
        # return the same physical ID to prevent delete on stack clenup 
        try:
            physicalID=event["PhysicalResourceId"]
            logger.info(f"Found physical ID {physicalID}") # "f
        except Exception as e:
            physicalID=str(uuid.uuid1())
            logger.info(f"Set physical ID {physicalID}") # "f
        
        cfnresponse.send(event, context, status, {}, physicalID)
