import re
import subprocess
from pprint import pprint
from typing import Tuple

ALLOWED_RECORDS: Tuple[str, ...] = ('TXT', 'A', 'MX', 'CNAME', 'AAAA', 'SOA',
                                    'DNAME', 'DS', 'NS', 'SRV', 'PTR', 'CAA',
                                    'TLSA')

DNS_SERVERS: Tuple[str, ...] = ('8.8.8.8', '1.1.1.1', 'ns1.hostiman.ru',
                                'ns2.hostiman.ru', 'ns3.hostiman.com',
                                'ns4.hostiman.com')


def dig(domain, record: str = 'A', custom_dns: tuple = ()) -> dict:
    """Main dig method, Returns information
    about the specified entry on the specified name servers.
    """
    if record:
        record = record.upper()
    if record not in ALLOWED_RECORDS:
        record = 'A'
    output = {
        'domain': domain,
        'record': record,
        'result': True,
        'data': {}
    }
    if custom_dns:
        ns_list = custom_dns
    else:
        ns_list = DNS_SERVERS
    for server in ns_list:
        output['data'][server] = []
        temp = subprocess.run(
            ['dig', '+noall', '+answer', domain, f'@{server}', record, '+time=3'],
            stdout=subprocess.PIPE
        )
        temp_output = temp.stdout.decode('utf-8')
        temp_output = re.sub('"', '', temp_output)
        for result in temp_output.splitlines():
            query = result.split(maxsplit=4)
            new_result = {
                'ttl': query[1],
                'content': query[4]
            }
            output['data'][server].append(new_result)
    return output


def test_dig(domain):
    a = []
    temp = subprocess.run(
        ['dig', '+noall', '+answer', domain, f'@8.8.8.8', 'TXT', '+time=3'],
        stdout=subprocess.PIPE
    )
    temp_output = temp.stdout.decode('utf-8')
    for result in temp_output.splitlines():
        output = result.split(maxsplit=4)
        new_result = {
            'ttl': output[1],
            'content': output[4]
        }
        a.append(new_result)
    print(a)


if __name__ == '__main__':
    a = dig('hostiman.ru', 'A')
    pprint(a)
    # test_dig('2241.ru')
