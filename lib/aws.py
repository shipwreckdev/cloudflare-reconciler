import boto3
import os

# AWS Credentials

ACCESS_KEY = os.getenv("ACCESS_KEY")
REGION = os.getenv("AWS_REGION")
SECRET_KEY = os.getenv("SECRET_KEY")

# Invoke one client for both elb and resourcegroupstaggingapi.

elb = boto3.client(
    'elb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION,
)

rtapi = boto3.client(
    'resourcegroupstaggingapi',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION,
)

# Get the DNS name of an ELB by providing the ELB name.


def GetELBHostname(name):
    try:
        response = elb.describe_load_balancers(
            LoadBalancerNames=[
                name,
            ]
        )

        return response['LoadBalancerDescriptions'][0]['DNSName']
    except:
        return 'Error: ELB not found with name {}'.format(name)

# Get the ARN of an ELB by using the resourcegroupstaggingapi to find the ELB using a provided tag key/value pair.


def GetELBARN(cluster, key, value):
    def lookup_for_tags(token):
        try:
            response = rtapi.get_resources(
                PaginationToken=token,
                TagFilters=[
                    {
                        'Key': key,
                        'Values': [value]
                    },
                    {
                        'Key': 'kubernetes.io/cluster/{}'.format(cluster),
                        'Values': ['owned']
                    }
                ],
                ResourcesPerPage=50,
                ResourceTypeFilters=[
                    'elasticloadbalancing:loadbalancer',
                ]
            )
            return response
        except Exception as e:
            print("Error when attempting to locate matching ELB: {}".format(e))

    total_results = []
    response = lookup_for_tags("")
    page_token = ""

    while True:
        total_results += response["ResourceTagMappingList"]
        page_token = response["PaginationToken"]
        if page_token == "":
            break
        response = lookup_for_tags(page_token)

    print(total_results)

    if total_results != []:
        return total_results[0]["ResourceARN"]
    else:
        return "Error: No load balancers found using the supplied tag {} with the value {}.".format(key, value)

# Package the logic here to return a single object.


def ReturnHostname(cluster, key, value):
    elb_arn = GetELBARN(cluster, key, value)

    elb_name = elb_arn.split('/')[1]

    return GetELBHostname(elb_name)
