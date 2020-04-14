"""
 Gets a boto3 session in the target account 
 
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""
import json, boto3, os


def get_session(targetAccount: str, roleName: str):

    roleArn="arn:aws:iam::" + targetAccount + ":role/" + roleName
    sts = boto3.client('sts')
    response = sts.assume_role(RoleArn=roleArn, RoleSessionName=TargetAccountSecurityRoleName+"_IR_lambda")
     
    session = boto3.Session(
                 aws_access_key_id=response['Credentials']['AccessKeyId'],
                 aws_secret_access_key=response['Credentials']['SecretAccessKey'],
     	         aws_session_token=response['Credentials']['SessionToken'])

    return session 
