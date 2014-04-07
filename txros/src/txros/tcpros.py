from __future__ import division

import struct

from twisted.protocols import basic

from txros import util

def deserialize_list(s):
    pos = 0
    res = []
    while pos != len(s):
        length, = struct.unpack('<I', s[pos:pos+4])
        if pos+4+length > len(s):
            raise ValueError('early end')
        res.append(s[pos+4:pos+4+length])
        pos = pos+4+length
    return res
def serialize_list(lst):
    return ''.join(struct.pack('<I', len(x)) + x for x in lst)

def deserialize_dict(s):
    res = {}
    for item in deserialize_list(s):
        key, value = item.split('=', 1)
        res[key] = value
    return res
def serialize_dict(s):
    return serialize_list('%s=%s' % (k, v) for k, v in s.iteritems())

class Server(basic.IntNStringReceiver):
    structFormat = '<I'
    prefixLength = struct.calcsize(structFormat)
    MAX_LENGTH = 2**32
    
    def __init__(self, handlers):
        self._handlers = handlers
        
        self.queue = None
    
    def stringReceived(self, string):
        if self.queue is None:
            # receive header
            header = deserialize_dict(string)
            self.queue = util.DeferredQueue()
            if 'service' in header:
                self._handlers['service', header['service']](header, self)
            elif 'topic' in header:
                self._handlers['topic', header['topic']](header, self)
            else:
                assert False
        else:
            self.queue.add(string)
    
    def connectionLost(self, reason):
        if self.queue is not None:
            self.queue.add(reason) # reason is a Failure

class Client(basic.IntNStringReceiver):
    structFormat = '<I'
    prefixLength = struct.calcsize(structFormat)
    MAX_LENGTH = 2**32
    
    def __init__(self):
        self.queue = util.DeferredQueue()
    
    def stringReceived(self, string):
        self.queue.add(string)
    
    def connectionLost(self, reason):
        self.queue.add(reason) # reason is a Failure
