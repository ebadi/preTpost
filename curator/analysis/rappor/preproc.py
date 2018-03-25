#!/usr/bin/python
#
# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Rappor preprocessing to generate a bloom filter
Taken from rappor.py
https://github.com/google/rappor/tree/master/client/python
"""

import hashlib
import struct
import sys
import configparser
sys.path.append('/libdp')
import libdp


def to_big_endian(i):
    """Convert an integer to a 4 byte big endian string.  Used for hashing."""
    # https://docs.python.org/2/lib/struct.html
    # - Big Endian (>) for consistent network byte order.
    # - L means 4 bytes when using >
    return struct.pack('>L', i)


def get_bloom_bits(word, cohort, num_hashes, num_bloombits):
    """Return an array of bits to set in the bloom filter.

    In the real report, we bitwise-OR them together.  In hash candidates,
    we put them in separate entries in the "map" matrix.
    """
    value = to_big_endian(cohort) + word  # Cohort is 4 byte prefix.
    md5 = hashlib.md5(value)

    digest = md5.digest()

    # Each has is a byte, which means we could have up to 256 bit Bloom filters.
    # There are 16 bytes in an MD5, in which case we can have up to 16 hash
    # functions per Bloom filter.
    if num_hashes > len(digest):
        raise RuntimeError("Can't have more than %d hashes" % md5)

    #  log('hash_input %r', value)
    #  log('Cohort %d', cohort)
    #  log('MD5 %s', md5.hexdigest())

    # python2 :
    # return [ord(digest[i]) % num_bloombits for i in xrange(num_hashes)]
    # python3 :
    return [digest[i] % num_bloombits for i in range(num_hashes)]


inFile = sys.argv[1]
outFile = sys.argv[2]
num_bloombits = int(sys.argv[3])
num_hashes = int(sys.argv[4])

data = configparser.ConfigParser()
data.read(inFile)

# python2 : secret = data['secret']['strx']
secret = str.encode(data['secret']['strx'])

cohort = 1

setBits = get_bloom_bits(secret, cohort, num_hashes, num_bloombits)
bloom = [0] * num_bloombits
for i in setBits:
    bloom[i] = 1

libdp.log('RAPPOR', secret=secret, bloombits=setBits, bloom=bloom)
libdp.toXml(outFile, bloom)
