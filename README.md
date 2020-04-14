# Introduction to performing automated incident response in a large, multi-account environment with exception handling
   
How quickly you respond to security incidents is key to minimizing their impacts. Automating incident response can help you scale your capabilities, rapidly reduce the scope of compromised resources, and reduce repetitive work by security teams. But when you use automation, you’ll also need to manage exceptions to standard response procedures.

This project provides a pattern and ready-made templates for a scalable multi-account setup of an automated incident response process with minimal code base, using native AWS tools. This project demonstrates how to set up exception handling for approved deviations based on resource tags. 

Important: Use caution when introducing automation. Carefully test each of the automated responses because automating a sub-optimal incident response process could be counterproductive.

## Solution

In this solution, you’ll use [AWS Systems Manager Automation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html) to execute most of the incident response steps. AWS maintains ready-made operational runbooks (automation documents), so you won’t need to maintain your own code base for them. The runbooks cover many predefined use cases, such as enabling Amazon Simple Storage Service (S3) bucket encryption, opening a Jira ticket, or terminating an Amazon Elastic Compute Cloud (EC2) instance. Every execution is well documented and repeatable in [AWS Systems Manager](https://aws.amazon.com/systems-manager/). For a few common cases where there were no ready-made automation documents, It is provided three additional AWS Lambda functions with the required response actions in the templates in this post. The Lambda functions require minimal code, with no external dependencies outside AWS native tools.

The code and automation runbooks are implemented in a central security account. You will use the central security account to execute the incident response actions. You won’t need to take any actions in the service accounts where you’re monitoring and responding to incidents.

For more information please see our **AWS Security Blog** on "Introduction to performing automated incident response in a large, multi-account environment with exception handling"

## How to deploy from Github

0) Clone the repo with `git clone [url]`

### Master Security Account 

1) Create a S3 bucket where the artifacts will be uploaded. Yor aws-cli-profile of master account must have read/write permission to the bucket. You can reuse existing bucket. It can be in the different region that the region you deploy. 

2) Adjust the Cloud Formation stack parameters in `./conf/master-acc.params.json`. You must NOT modify the parameters S3BucketSources and S3SourcesPrefix as they are adjusted by deployment script.  

3) Deploy by executing `./scripts/deploy.sh` with type parameter *master*, *S3 bucket*, *aws-cli-profile* and *region*. It will upload the artifacts to the S3 bucket and will deploy the Cloud Formation stack. 

Usage:  `./deploy.sh account_type[master|service] s3://bucket aws-cli-profile aws-region`

Example of execution 
```
./deploy.sh master s3://sources.sec.ir.sample SecMaster-2 eu-west-3

updating: isolate_ec2_lambda_function.py (deflated 61%)
updating: start_ssm_automation_lambda_function.py (deflated 57%)
updating: confine_secgr_lambda_function.py (deflated 64%)
updating: security_hub.py (deflated 55%)
updating: notify.py (deflated 42%)
updating: security_hub_custom_actions.py (deflated 68%)
updating: cfnresponse.py (deflated 58%)
updating: account_session.py (deflated 50%)
updating: session.py (deflated 51%)
updating: guard_duty.py (deflated 63%)
updating: deactivate_principal_lambda_function.py (deflated 67%)
upload: src/cfn/master-acc/master-account-custom-actions-sec-hub.yaml to s3://sources.sec.ir.sample/master/master-account-custom-actions-sec-hub.yaml
upload: src/cfn/master-acc/copy-s3obj-to-regional-s3bucket.yaml to s3://sources.sec.ir.sample/master/copy-s3obj-to-regional-s3bucket.yaml
upload: src/cfn/master-acc/master-account-main.yaml to s3://sources.sec.ir.sample/master/master-account-main.yaml
upload: dist/master_lambda_functions.zip to s3://sources.sec.ir.sample/master/master_lambda_functions.zip
resource uploaded successfully to s3://sources.sec.ir.sample

going to create-stack
arn:aws:cloudformation:eu-west-3:160815017796:stack/IR-master-account-stack/f29a6970-7299-11ea-bf0e-0e3a535926a2
Waiting for CF  stack to finish ..........................................
Stack IR-master-account-stack created (status CREATE_COMPLETE) 
``` 

### Service Account 

1) Create or reuse a S3 bucket where the artifacts will be uploaded. Yor aws-cli-profile of service account must have read/write permissions to the bucket. You can reuse existing bucket for sure. It can be in the different region that the region you deploy. 

2) Adjust the Cloud Formation stack parameters in `./conf/service-acc.params.json`. You must NOT modify the parameters S3BucketSources and S3SourcesPrefix as they are adjusted on deployment.

3) Execute `./deploy.sh` script with type parameter *service*, *S3 bucket*, *aws-cli-profile* and *region*. It will upload the artifacts to the S3 bucket and will deploy the Cloud Formation stack 

Example:
```
./deploy.sh service s3://sources.sec.ir.sample SecEnv-2 eu-west-3
...
...
```
