#!/usr/bin/env python
import argparse, netbox

parser = argparse.ArgumentParser(description='Import data to Database.')


parser.add_argument('--nbdump',
                    help='Option to dump data from netbox')
parser.add_argument('--objects',
                    help="""Option to select which objects to add. 
                    Options: {tenant, site, bldg, room, 
                    rack, device, subdevice, subdevice1}.
                    Note they are inclusive (ie specifying subdevices
                    will import everything until subdevices""")

parser.add_argument('--url',
                    help='Option to dump data from netbox')
parser.add_argument('--dumpdir',
                    help="""Location to store JSON results.
                    All results will be stored in a text file named 
                    \'nbout.txt\'""")
args = parser.parse_args()
#print(args.accumulate(args.integers))