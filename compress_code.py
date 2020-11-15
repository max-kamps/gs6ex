"""Compresses a file for use with the execc command"""

import sys
import modules.compress as cc

if len(sys.argv) < 2:
    exit(f'Usage: python {sys.argv[0]} <path>')

with open(sys.argv[1]) as f:
    source = f.read()

print(cc.base32768_encode_bytes(source.encode()))

# print(len(source.encode('utf-16'))//2)
# print(len(cc.base32768_encode_bytes(source.encode())))
# print(len(cc.base32768_encode_object(source)))
