import argparse
import json
import os
import requests
import lib.cf as cf
import lib.aws as aws
import lib.gh as gh

version = "v1.0"

api_base = 'https://api.cloudflare.com/client/v4/zones'
api_key = os.getenv("CLOUDFLARE_API_KEY")
content_type = 'application/json'
email = os.getenv("CLOUDFLARE_EMAIL")
github_repo = "mygithuborg/myrepo"

# Parse for arguments.
parser = argparse.ArgumentParser(
    description='Compare records in Cloudflare against endpoints in AWS and reconcile resources that do not match.')
parser.add_argument('--cluster', dest='cluster', type=str,
                    help='EKS cluster to use when looking for load balancers. Should be Name tag of cluster.', default='')
parser.add_argument('--dry-run', dest='dry_run',
                    help='Dry run mode. Records will not be reconciled in Cloudflare with this option.', action='store_true')
parser.add_argument('--domain', dest='domain', type=str,
                    help='Domain to evaluate. For example: foobar.com', default='')
parser.add_argument('--elb-tag', dest='elb_tag', type=str,
                    help='Tag key/value used to find load balancer in the form of key:value.', default='')
parser.add_argument('--issue', dest='create_issue',
                    help='Create a GitHub issue in the subject Terraform repository with relevant data.', action='store_true')
parser.add_argument('--records', dest='records', type=str,
                    help='Record to evaluate. For example: test - this would imply test.foobar.com', default='')

args = parser.parse_args()

# Establish argument variables.
cluster = args.cluster
create_issue = args.create_issue
dry_run = args.dry_run
domain = args.domain
elb_tag = args.elb_tag.split(':')
records = args.records.split(',')

headers = {
    'X-Auth-Email': email,
    'X-Auth-Key': api_key,
    'Content-Type': content_type
}

zones = cf.GetZones(api_base, headers)

if dry_run:
    print('Dry run enabled. Unsynchronized Cloudflare records will not be updated.')
    print()

if __name__ == "__main__":
    if domain != '' and elb_tag != [''] and cluster != '':
        if domain in zones.keys():
            if records != ['']:
                for r in records:
                    print('Evaluating {}.{}'.format(r, domain))
                    print()

                    status = cf.GetExistingRecord(
                        api_base, domain, headers, r, zones[domain])

                    if type(status) is dict:
                        print('Cloudflare Record: ' + status['host'])
                        print('Cloudflare Record Type: ' +
                              status['record_type'])
                        print('Cloudflare Record Content: ' +
                              status['content'])
                        print()

                        current_elb_hostname = aws.ReturnHostname(cluster,
                                                                  elb_tag[0], elb_tag[1])

                        print('ELB Hostname: ' + current_elb_hostname)
                        print()

                        if status['content'] == current_elb_hostname:
                            synchronized = True
                        else:
                            synchronized = False

                        print('Synchronized: ' + str(synchronized))
                        print()

                        if synchronized == False and dry_run == False:
                            action = cf.UpdateRecord(
                                api_base, headers, current_elb_hostname, status, zones[domain])
                            print(action)

                            if create_issue == True:
                                print()
                                gh.create_issue(
                                    "[cloudflare-reconciler] Record {} needs to be updated in Cloudflare.".format(
                                        status['host']),
                                    "The Cloudflare record `{}` should be updated in Terraform to point to the endpoint `{}` which has recently changed.\n\nThis issue was automatically created by `cloudflare-reconciler {}`.".format(status['host'], current_elb_hostname, version))
                        elif synchronized == False and dry_run == True:
                            print(
                                'Record is not synchronized. Skipping update since dry run is enabled.')
                    else:
                        print('{} in Cloudflare zone {}'.format(status, domain))
            else:
                print(
                    'Please provide at least one record to evaluate for {}.'.format(domain))
        else:
            print('No matching zone found for domain {}.'.format(domain))
            print()
            print('Available Cloudflare zones: ')
            for k in zones.keys():
                print(k)
    else:
        print('Please provide a domain to evaluate, a key/value pair for isolating an AWS ELB, and an EKS cluster option.')
