#!/usr/bin/env python

# Requires https://github.com/bitly/bitly-api-python

import csv
import getopt
import requests
import sys
import types
import urllib

def main(argv=None):
    """
    This script exports all Bit.ly urls for an account.
    
    Required options:
        -t=, --token=: Bit.ly OAuth token
    
    Optional parameters:
        -v: Verbose mode
        -h: Display this help and exit
    """
    # Load options using getopt
    if argv is None:
        argv = sys.argv
    
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "vht:o:",
            ["help", "token=", "output="]
        )
    except getopt.error, msg:
        print "Option parsing error: %s" % str(msg)
        return 2
    
    # Setup defaults
    verbose = False
    access_token = None
    output_path = 'links.csv'
    
    try:
        for option, value in opts:
            if option == "-v":
                verbose = True
            elif option in ("-h", "--help"):
                print main.__doc__
                return 0
            elif option in ("-t", "--token"):
                access_token = value
            elif option in ("-o", "--output"):
                output_path = value
            else:
                raise Exception('unknown option')
    except Exception, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err)
        print >> sys.stderr, "\t for help use --help"
        return 2
    
    if access_token is None:
        raise Exception('Token parameter must be present.')
    
    bitly = Bitly(access_token, verbose)
    
    limit = 100
    offset = 0
    result_count = 0
    nb_found = 0
    
    csv_writer = csv.writer(open(output_path, 'wb'), quoting=csv.QUOTE_ALL)
    csv_writer.writerow(('Link', 'Long url'))

    while offset <= result_count:
        data = bitly.user_link_history(limit=limit, offset=offset, access_token=access_token)
    
        result_count = data['result_count']
        
        for link in data['link_history']:
            csv_writer.writerow((link['link'], link['long_url'].encode('utf8')))
            
            nb_found += 1
        
        offset += limit
        
        if verbose:
            progress = float(offset) / result_count
            
            sys.stdout.write("\r(%2d%%) Loaded %5d/%5d links..." % (
                round(progress * 100), offset, result_count
            ))
            sys.stdout.flush()
    
    if verbose:
        print ""
        print "Done! Found %d links, expected %d." % (nb_found, result_count)

class Bitly(object):
    def __init__(self, access_token, verbose=False):
        super(Bitly, self).__init__()
        self.access_token = access_token
        self.verbose = verbose
        
    def user_link_history(self, limit=50, offset=0, access_token=None):
        params = {
            'limit': limit,
            'offset': offset,
            'archived': 'both'
        }
    
        return self._call('v3/user/link_history', params)['data']

    def _call(self, method, params):
        """
        A good chunk of the following method has been extracted from
        https://github.com/bitly/bitly-api-python
        """
        params['access_token'] = self.access_token
        
        # force to utf8 to fix ascii codec errors
        encoded_params = []
        for k,v in params.items():
            if type(v) in [types.ListType, types.TupleType]:
                v = [e.encode('UTF8') for e in v]
            else:
                v = str(v).encode('UTF8')
            encoded_params.append((k,v))
        params = dict(encoded_params)
        
        request = "https://api-ssl.bitly.com/%(method)s?%(params)s" % {
            'method': method,
            'params': urllib.urlencode(params, doseq=True)
        }
        
        http_response = requests.get(request, timeout=10)
        
        if http_response.status_code != 200:
            raise Exception('HTTP %d Error: %s' % (http_response.status_code, http_response.text))
        
        data = http_response.json()
        
        if data is None or data.get('status_code', 500) != 200:
            raise Exception('Bitly returned error code %d: %s' % (data.get('status_code', 500), data.get('status_txt', 'UNKNOWN_ERROR')))
        
        return data

if __name__ == '__main__':
    sys.exit(main())
