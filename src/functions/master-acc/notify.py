"""
 Send notification
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
import json, boto3, os, logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def sendNotification(msg: str):
    AlertsSns=os.environ['AlertsSns'] 
    
    client = boto3.client('sns')
    response = client.publish(
       TopicArn=AlertsSns,
       Message=msg )

    logger.info(msg) 
