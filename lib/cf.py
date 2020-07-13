import json
import os
import requests

# Look up an existing Cloudflare record and return its value.


def GetExistingRecord(api_base, domain, headers, record, zone):
    params = {'name': "{}.{}".format(record, domain)}

    r = requests.get('{}/{}/dns_records'.format(api_base,
                                                zone), params=params, headers=headers)

    p = json.loads(r.text)

    if p['result'] != []:
        return {'host': p['result'][0]['name'], 'id': p['result'][0]['id'], 'record_type': p['result']
                [0]['type'], 'content': p['result'][0]['content'], 'proxied': p['result'][0]['proxied']}
    else:
        return "No matching record found for {}.{}".format(record, domain)


def GetZones(api_base, headers):
    r = requests.get('{}'.format(api_base), headers=headers)

    p = json.loads(r.text)

    if p['result'] != []:
        zone_dict = {}

        for zone in p['result']:
            zone_dict.update(
                {'{}'.format(zone['name']): '{}'.format(zone['id'])})

        return zone_dict
    else:
        return "No zones found."

# Write new value for a given record if unsynchronized.


def UpdateRecord(api_base, headers, new_record_value, ret, zone):
    data = json.dumps({'type': ret['record_type'], 'name': ret['host'],
                       'content': new_record_value, 'ttl': 1, 'proxied': ret['proxied']})

    print("Updating Cloudflare {} record {} to {}...".format(
        ret['record_type'], ret['host'], new_record_value))

    r = requests.put('{}/{}/dns_records/{}'.format(api_base, zone,
                                                   ret['id']), headers=headers, data=data)

    return json.loads(r.text)
