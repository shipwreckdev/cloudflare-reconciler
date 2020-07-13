# Cloudflare Reconciler

Uses input to look up a configured Cloudflare record, return its current value, compare the value to the current hostname of an Elastic Load Balancer, and update the record if it is not accurate.


## Purpose

This tool will compare Cloudflare DNS records to resources in other providers and platforms. It was originally built to automatically update Cloudflare `CNAME` records when Amazon ELBs associated with Kubernetes `Service` objects change. This is useful to help reconcile records quickly in the event a load balancer is destroyed and recreated.

## Usage

```bash
usage: main.py [-h] [--cluster CLUSTER] [--dry-run] [--domain DOMAIN]
               [--elb-tag ELB_TAG] [--issue] [--records RECORDS]

Compare records in Cloudflare against endpoints in AWS and reconcile resources
that do not match.

optional arguments:
  -h, --help         show this help message and exit
  --cluster CLUSTER  EKS cluster to use when looking for load balancers.
                     Should be Name tag of cluster.
  --dry-run          Dry run mode. Records will not be reconciled in
                     Cloudflare with this option.
  --domain DOMAIN    Domain to evaluate. For example: foobar.com
  --elb-tag ELB_TAG  Tag key/value used to find load balancer in the form of
                     key:value.
  --issue            Create a GitHub issue in the subject Terraform repository
                     with relevant data.
  --records RECORDS  Record to evaluate. For example: test - this would imply
                     test.foobar.com
```

## Environment Variables

The application depends on these environment variables to run:

* `ACCESS_KEY` - AWS access key for the target account.
* `AWS_REGION` - AWS region for the target account.
* `CLOUDFLARE_API_KEY` - The API token for the Cloudflare user with access rights to make changes within the Cloudflare account.
* `CLOUDFLARE_EMAIL` - The email address associated with the Cloudflare user.
* `GITHUB_REPO` - The GitHub repository in the form of `org/repo` if generating issues.
* `GITHUB_ACCESS_TOKEN` - GitHub access token for use by the app to generate an issue.
* `SECRET_KEY` - AWS secret key for the target account.

### Example

```bash
python3 main.py --domain foobar.com --records mytest --elb-tag kubernetes.io/service-name:default/test-service --cluster staging
```

### Process

The logic is as follows:

* Evaluate the domain `foobar.com`
* Evaluate the record `mytest`
* These combine to form `mytest.foobar.com`
* Retrieve the value for the Cloudflare DNS record `mytest.foobar.com`
* Retrieve the Elastic Load Balancer using the tag `Key: kubernetes.io/service-name, Value: default/test-service`
* Use the ARN of the ELB to describe the ELB and find its current DNS/hostname
* Compare the current DNS/hostname of the ELB to the Cloudflare record
* If the Cloudflare record value is not up to date with the latest ELB hostname, update it

## Application Output

When not running the application using the `--dry-run` flag, you will receive one of two responses from Cloudflare - success or error.

### Success

```bash
Evaluating mytest.foobar.com

Cloudflare Record: mytest.foobar.com
Cloudflare Record Type: CNAME
Cloudflare Record Content: a2352-23r2eg-old.us-east-1.elb.amazonaws.com

ELB Hostname: a2352-23r2eg-correct-2.us-east-1.elb.amazonaws.com

Synchronized: False

Updating Cloudflare CNAME record mytest.foobar.com to a2352-23r2eg-correct-2.us-east-1.elb.amazonaws.com...
{'result': {'id': '1234', 'zone_id': '1234', 'zone_name': 'foobar.com', 'name': 'mytest.foobar.com', 'type': 'CNAME', 'content': 'a2352-23r2eg-correct-2.us-east-1.elb.amazonaws.com', 'proxiable': True, 'proxied': True, 'ttl': 1, 'locked': False, 'meta': {'auto_added': False, 'managed_by_apps': False, 'managed_by_argo_tunnel': False, 'source': 'primary'}, 'created_on': 'timestamp', 'modified_on': 'timestamp'}, 'success': True, 'errors': [], 'messages': []}
```

### Failure

```bash
Evaluating mytest.foobar.com

Cloudflare Record: mytest.foobar.com
Cloudflare Record Type: CNAME
Cloudflare Record Content: a2352-23r2eg-old.us-east-1.elb.amazonaws.com

ELB Hostname: a2352-23r2eg-correct-2.us-east-1.elb.amazonaws.com

Synchronized: False

Updating Cloudflare CNAME record mytest.foobar.com to a2352-23r2eg-correct-2.us-east-1.elb.amazonaws.com...
{'result': None, 'success': False, 'errors': [{'code': 9207, 'message': 'Failed to parse request body, content-type must be application/json'}], 'messages': []}
```

The failure message is provided only as an example - error messages will vary.
