import functools
from numpy import little_endian, uint, uint64
from lmt import Lmt
import bitstring
import struct
import numpy as np

def unpack_bytes(b):
    return b.int/((1<<(len(b)-2))-1)

def pack_bytes(bitcount, f):
    bitmask2 = ((2**(bitcount))-1)
    bitmask3 = ((2**(bitcount-2))-1)

    r = (int(f * bitmask3) + 2**bitcount) & bitmask2

    return bitstring.Bits(uint=r, length=bitcount)

'''
def unpack_bytes2(b):
    bitcount = len(b)
    return b.uint/((2**bitcount)-1)

def pack_bytes2(bitcount, f):
    r = int(f*((2**bitcount)-1))
    r = bitstring.BitStream(r)[0:bitcount]
    return r

def preprocess4_11(b):
    return  b[37:48] + \
            b[32:37] + b[26:32] + \
            b[16:26] + b[15:16] + \
            b[4:15]

def preprocess4_9(b):
    return  b[32:40] + b[31:32] + \
            b[24:31] + b[22:24] + \
            b[16:22] + b[13:16] + \
            b[8:13]  + b[4:8]
'''

def vec3to4(d):
    return [d[0],d[1],d[2],1]

def vec3to4Q(d):
    return [d[0],d[1],d[2], np.sqrt(1-d[0]*d[0]-d[1]*d[1]-d[2]*d[2])]

def vec4to3(d):
    return d[0:3]

def id(d):
    return d

def buffer2bits(d):
    return bitstring.Bits(bytes=d)

def buffer2bits2(d):
    return bitstring.Bits(bytes=d[::-1])

def padding(pad):
    return lambda d: bitstring.Bits(length=pad) + d

def xwto4(d):
    return [d[0], 0, 0, d[1]]

def ywto4(d):
    return [0, d[0], 0, d[1]]

def zwto4(d):
    return [0, 0, d[0], d[1]]

def constant1(b): return 1

def noop_frame(b, frame): return b

def get_frame(start, len):
    return lambda b: b[start:(start+len)].uint

def put_frame(start, len):
    return lambda b, frame: b[0:start] + bitstring.Bits(uint=frame,length=len) + b[(start+len):]

float_format = {
    "unpack": lambda b: b.floatle,
    "pack": lambda bitcount, f: bitstring.Bits(floatle=f, length=bitcount)
}

unsigned_format = {
    "unpack": lambda b: b.uint/((2**len(b))-1),
    "pack": lambda bitcount, f: bitstring.Bits(uint=uint(f*((2**bitcount)-1)), length=bitcount)
}

signed_format = {
    "unpack": unpack_bytes,
    "pack": pack_bytes
}

basic_preprocess = {"unpack": buffer2bits, "pack": lambda b: b.bytes}
invert_preprocess = {"unpack": buffer2bits2, "pack": lambda b: b.bytes[::-1]}

post_process_vec3 = {"unpack": vec3to4, "pack": vec4to3}
post_process_vec3Q = {"unpack": vec3to4Q, "pack": vec4to3}
no_post_process = {'unpack': id, "pack": id}

no_frame = {"unpack": constant1, "pack": noop_frame }
def has_frame(start,end):
    return {"unpack": get_frame(start,end), "pack": put_frame(start,end) }

constants = {
    Lmt.Track.Compression.singlevector3: 
    {"buffer_size": 12, "bit_size": 32, "strides":[0,32,64], 
    "format": float_format, "frames": no_frame,
    "preprocess": basic_preprocess, "postprocess": post_process_vec3},
    Lmt.Track.Compression.singlerotationquat3: 
    {"buffer_size": 12, "bit_size": 32, "strides":[0,32,64], 
    "format":float_format, "frames": no_frame,
    "preprocess": basic_preprocess, "postprocess": post_process_vec3Q},
    Lmt.Track.Compression.linearvector3: 
    {"buffer_size": 16, "bit_size": 32, "strides":[0,32,64,96], 
    "format":float_format, "frames": no_frame,
    "preprocess": basic_preprocess, "postprocess": no_post_process},
    Lmt.Track.Compression.bilinearvector3_16bit: 
    {"buffer_size": 8, "bit_size": 16, "strides":[48,32,16], 
    "format": unsigned_format, "frames": has_frame(0,16),
    "preprocess": invert_preprocess, "postprocess": post_process_vec3},
    Lmt.Track.Compression.bilinearvector3_8bit: 
    {"buffer_size": 4, "bit_size": 8, "strides":[0,8,16], 
    "format": unsigned_format, "frames": has_frame(24,8),
    "preprocess": basic_preprocess, "postprocess": post_process_vec3},
    Lmt.Track.Compression.linearrotationquat4_14bit: 
    {"buffer_size": 8, "bit_size": 14, "strides":[8,22,36,50],
    "format": signed_format, "frames": has_frame(0,8),
    "preprocess": invert_preprocess, "postprocess": no_post_process},
    Lmt.Track.Compression.bilinearrotationquat4_7bit: 
    {"buffer_size": 4, "bit_size": 7, "strides":[4,11,18,25],
    "format": unsigned_format, "frames": has_frame(0,4),
    "preprocess": invert_preprocess, "postprocess": no_post_process}
}

'''
Lmt.Track.Compression.bilinearrotationquatxw_14bit: 
{"buffer_size": 4, "strides":[18,14,4,14], 
"format":unpack_bytes2, "unformat": pack_bytes2,
"preprocess": id, "unpreprocess": padding,
"postprocess": xwto4, "unpostprocess":id},
Lmt.Track.Compression.bilinearrotationquatyw_14bit: 
{"buffer_size": 4, "strides":[18,14,4,14], 
"format":unpack_bytes2, "unformat": pack_bytes2,
"preprocess": id, "unpreprocess": id,
"postprocess": ywto4, "unpostprocess":id},
Lmt.Track.Compression.bilinearrotationquatzw_14bit: 
{"buffer_size": 4, "strides":[18,14,4,14], 
"format":unpack_bytes2, "unformat": pack_bytes2,
"preprocess": id, "unpreprocess": id,
"postprocess": zwto4, "unpostprocess":id},
Lmt.Track.Compression.bilinearrotationquat4_11bit: 
{"buffer_size": 6, "strides":[33,11,22,11,11,11,0,11], "format":unpack_bytes2, "preprocess": preprocess4_11, "postprocess": id},
Lmt.Track.Compression.bilinearrotationquat4_9bit: 
{"buffer_size": 5, "strides":[0,9,9,9,18,9,27,9], "format":unpack_bytes2, "preprocess": preprocess4_9, "postprocess": id},
'''

def process(compressor, buffer, extremes):
    strides = compressor['strides']
    bit_size = compressor['bit_size']

    preprocess = compressor['preprocess']
    format = compressor["format"]
    postprocess = compressor['postprocess']
    frames_process = compressor['frames']

    assert(compressor["buffer_size"]==len(buffer))

    c2 = preprocess['unpack'](buffer)
    bin_vec = [c2[s:(s+bit_size)] for s in strides]
    vec = [format['unpack'](bv) for bv in bin_vec]
    #for bv,v in zip(bin_vec,vec):
    #    print(bv, v, end=' ')
    #print()
    result = postprocess['unpack'](vec)
    frames = frames_process['unpack'](c2)

    #### assert ####
    '''
    unvec = postprocess['pack'](result)
    temp = bitstring.Bits(length=compressor["buffer_size"]*8)
    temp_vec = [format['pack'](bit_size, b) for b in unvec]
    for s, v in zip(strides,temp_vec):
        temp = temp | (
            (bitstring.Bits(length=s)) + v + 
            (bitstring.Bits(length=len(temp)-s-bit_size)))
    temp = frames_process['pack'](temp,frames)
    unc = preprocess['pack'](temp)
    unc = bitstring.Bits(unc)

    assert(unc==bitstring.Bits(bytes(buffer)))
    '''
    #### assert ####

    if not extremes is None:
        result = np.add(extremes.max, np.multiply(extremes.min,result))

    return result, frames

def process_buffer(codec, buffer, extremes):

    compressor = constants[codec]
    size = compressor['buffer_size']
    return [process(compressor,buffer[s:(s+size)],extremes) for s in range(0,len(buffer),size)]

if __name__ == "__main__":
    '''
    i = 0
    while i < (1 << 14):
        print(i, i/((1<<13)-1))
        i += 0x100

    exit()
    '''
    print(0.2705408375045782)
    print(pack_bytes(14, unpack_bytes(bitstring.Bits(bin='0b00010001010100')))) #, 
    print(-0.270785007935539)
    print(pack_bytes(14, unpack_bytes(bitstring.Bits(bin='0b11101110101011')))) #, 
    print(-0.6534000732511293)
    print(pack_bytes(14, unpack_bytes(bitstring.Bits(bin='0b11010110001100')))) #, 
    print(0.6531559028201684)
    print(pack_bytes(14, unpack_bytes(bitstring.Bits(bin='0b00101001110011')))) #, 

    codec = [   Lmt.Track.Compression.singlevector3,
                Lmt.Track.Compression.singlerotationquat3,
                Lmt.Track.Compression.linearvector3,
                Lmt.Track.Compression.bilinearvector3_16bit,
                Lmt.Track.Compression.bilinearvector3_8bit,
                Lmt.Track.Compression.linearrotationquat4_14bit,
                Lmt.Track.Compression.bilinearrotationquat4_7bit,
                Lmt.Track.Compression.bilinearrotationquatxw_14bit,
                Lmt.Track.Compression.bilinearrotationquatyw_14bit,
                Lmt.Track.Compression.bilinearrotationquatzw_14bit,
                Lmt.Track.Compression.bilinearrotationquat4_11bit,
                Lmt.Track.Compression.bilinearrotationquat4_9bit]


    '0.270600,-0.270600,-0.653280,0.653280=FF7F42EEACD7D200'
    """"""

    testdata = """0.270600,-0.270600,-0.653280,0.653280=158C8A3E158C8ABE5C3D27BF
5.563200,12.846931,368.251892,1.000000=BC05B240088D4D413E20B843
5.563200,12.846931,368.251892,1.000000=BC05B240088D4D413E20B84300000000
0.563200,0.846931,0.251900,1.000000=2D90CFD87C400000
0.563200,0.846931,0.251900,1.000000=8FD74000
0.270600,-0.270600,-0.653280,0.653280=730A63BDBA531100
0.270600,0.270600,0.653280,0.653280=D3A94804
0.270600,0.270600,0.653280,0.653280=51D1730A
0.270600,0.270600,0.653280,0.653280=51D1730A
0.270600,0.270600,0.653280,0.653280=CFE9730A
0.270600,0.270600,0.653280,0.653280=294229A7730A
0.270600,0.270600,0.653280,0.653280=4544A6A50D"""

    for pos, line in enumerate(testdata.splitlines(False)):
        input_str, buffer_str = line.split("=")
        input = [float(i) for i in input_str.split(',')]
        print('---------------------------')
        print(input)

        buffer = bytes.fromhex(buffer_str)

        #print(buffer,len(buffer))

        print(codec[pos])

        print(process_buffer(codec[pos], list(buffer), None))


