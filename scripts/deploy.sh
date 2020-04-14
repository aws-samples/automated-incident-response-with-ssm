#
# Deploys the IR samples in an account 
#
#   - Zips the Lambda-functions. 
#   - Uploads the CFNs and ZIP to S3 Bucket 
#   - Starts the CFN
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
set -e 

print_usge (){
	
	echo "Usage:   ./deploy [master|service] s3://s3bucket aws-cli-profile aws-region"
	echo "Example: ./deploy.sh master s3://mybucket myprofile eu-west-1"
	echo 
}

if [ -z $1 ] || ( [ "$1" != "master" ] && [ "$1" != "service" ] ); then 
	echo "Error: provide as first(1) param type of account [master or service]"
	print_usge
	exit 1
else 
	type=$1
fi

if [ -z $2 ]; then 
	echo "Error: provide as second(2) param target bucket without prefix"
	print_usge
	exit 2
else 
	bucket=$2
fi

if [ -z $3 ]; then 
	echo "Error: provide as third(3) param the AWS CLI profle"
	print_usge
	exit 3
else
	profile=$3
fi

if [ -z $4 ]; then 
	echo "Error: provide as fourth(4) param the AWS region"
	print_usge
	exit 4
else
	region=$4
fi

cd ..
if  [ "${bucket: -1}" = "/" ]; then 
	bucket="${bucket%%/}"
	echo "removed slash at the end of $bucket" 
fi

zip -jr  "./dist/${type}_lambda_functions.zip"     "./src/functions/${type}-acc"
aws s3 cp --exclude ".*" --recursive "./src/cfn/${type}-acc/"   "$bucket/${type}" --profile "$profile" --region "$region"
aws s3 cp "./dist/${type}_lambda_functions.zip"  "$bucket/${type}/" --profile "$profile" --region "$region"
echo "resource uploaded successfully to ${bucket}"

prefix="${type}/"
# Add source bucket and prefix 
b=${bucket#*//}
sed "s/{S3BucketSources}/${b}/" ./conf/${type}-acc.params.json | sed "s|{S3SourcesPrefix}|${prefix}|" > "./dist/.tmp.param.json"
stackName="IR-${type}-account-stack"

#
# check if create-stack or update
#
set +e
out=$(aws cloudformation describe-stacks --stack-name $stackName --region $region --profile $profile --output text &> /dev/null )

if [ $? -eq 0 ] ; then
  CREATE_OR_UPDATE="update-stack"
else
  CREATE_OR_UPDATE="create-stack"
fi
set -e 

echo ""
echo  "going to $CREATE_OR_UPDATE"

aws cloudformation $CREATE_OR_UPDATE \
    --stack-name $stackName \
    --template-body "file://src/cfn/${type}-acc/${type}-account-main.yaml" \
    --parameters "file://dist/.tmp.param.json" \
    --region $region \
    --profile $profile \
    --output text \
    --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM CAPABILITY_NAMED_IAM

printf "Waiting for CF $steakName stack to finish ..."
cfStat="start"
while [[ "$cfStat" != "CREATE_COMPLETE"  ]] && [[ "$cfStat" != "UPDATE_COMPLETE" ]]
do
  sleep 3
  printf "."
  cfStat=$(aws cloudformation describe-stacks --stack-name $stackName --region $region --profile $profile  --query 'Stacks[0].[StackStatus]' --output text)
  if [ "$cfStat" = "CREATE_FAILED" ] || [[ "$cfStat" == *"ROLLBACK"* ]]
  then
    printf "\nError: Stack $stackName failed to create or update\n"
    exit 5
  fi
done
printf "\nStack $stackName created (status $cfStat) \n"
	
