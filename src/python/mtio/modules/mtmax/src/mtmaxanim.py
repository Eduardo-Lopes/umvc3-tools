import os
from typing import List
import mtmaxconfig, mtmaxutil
from pymxs import runtime as rt
import pymxs as mx

from mtmaxrollout import MtRollout

import mtmaxlog
import lmt
import codec
import numpy as np

import struct

np.set_printoptions(suppress=True)

packer_s1 = struct.Struct('b')
packer_s2le = struct.Struct('<h')
packer_s4le = struct.Struct('<i')
packer_s8le = struct.Struct('<q')

packer_u1 = struct.Struct('B')
packer_u2le = struct.Struct('<H')
packer_u4le = struct.Struct('<I')
packer_u8le = struct.Struct('<Q')

packer_f4le = struct.Struct('<f')

def write_lmt(lmt, f):

    allocator_pointer = 0

    f.write(lmt.magic)
    f.write(packer_s2le.pack(lmt.version))
    f.write(packer_s2le.pack(lmt.entrycount))

    #print(f'\tversion: {lmt.version}')
    #print(f'\tentries: {lmt.entrycount}')

    allocator_pointer = 8+lmt.entrycount*8

    motions_pointer = 8

    motion_table = []

    for motion_idx, motion in enumerate(lmt.entries):
        #print(f'\tentry {motion_idx}:')

        if motion.entry is None:
            motion_table.append(0)
        else:
            # 16 bits alignment
            allocator_pointer = (allocator_pointer+15)&~15
            motion_table.append(allocator_pointer)
            allocator_pointer += 88

    track_pointer = 0
    eventclasses_pointer = 0
    first_track_pointer = 0

    for motion_idx, motion in enumerate(lmt.entries):

        motions_pointer += 8

        if motion.entry is None:
            f.write(packer_s8le.pack(0))
        else:
            #allocator_pointer = (allocator_pointer+15)&~15

            entry_pointer = motion_table[motion_idx]

            f.write(packer_s8le.pack(entry_pointer))
            #entry_pointer = allocator_pointer
            #allocator_pointer += 88

            entry : lmt.Lmt.Animentry = motion.entry

            #print(f'\t\ttracks: {entry.trackcount}')

            #trackptr
            def fill_track_table():
                nonlocal allocator_pointer
                nonlocal entry
                if entry.trackcount == 0:
                    return 0
                else:
                    #f.write(packer_s8le.pack(allocator_pointer))
                    result_pointer = allocator_pointer 
                    track_pointer = allocator_pointer
                    allocator_pointer += 48 * entry.trackcount

                    extremes_table = []
                    track: lmt.Lmt.Track
                    for track_idx, track in enumerate(entry.tracklist):
                        #write extreme
                        if track.extremes is None:
                            extremes_table.append(0)
                        else:
                            allocator_pointer = (allocator_pointer+15)&~15
                            extremes_table.append(allocator_pointer)
                            f.seek(allocator_pointer)
                            allocator_pointer += 4*4+4*4

                            extreme : lmt.Lmt.Extreme = track.extremes

                            for elem in extreme.min:
                                f.write(packer_f4le.pack(elem))
                            for elem in extreme.max:
                                f.write(packer_f4le.pack(elem))

                    buffer_table = []
                    for track_idx, track in enumerate(entry.tracklist):
                        if track.buffersize == 0:
                            buffer_table.append(0)
                        else:
                            buffer_table.append(allocator_pointer)
                            f.seek(allocator_pointer)
                            allocator_pointer += track.buffersize
                            #write buffer
                            for buffer_elem in track.buffer:
                                f.write(packer_u1.pack(buffer_elem))
                            f.seek(track_pointer+24)

                    f.seek(track_pointer)

                    #write tracks
                    track: lmt.Lmt.Track
                    for track_idx, track in enumerate(entry.tracklist):

                        '''
                        print(f'\t\t\ttrack {track_idx}: type: {track.buffertype.name}')

                        if track.buffersize != 0:
                            constant = constants[track.buffertype]
                            assert(track.buffersize % constant['size'] == 0)
                            if track.buffertype == Lmt.Track.Compression.bilinearvector3_16bit:
                                data = np.reshape(track.buffer, (-1,8))
                                def process(d):
                                    data = [d[1]<<8|d[0],d[3]<<8|d[2],d[5]<<8|d[4],d[7]<<8|d[6]]
                                    data = np.multiply(data,[1/(256*256-1),1/(256*256-1),1/(256*256-1),1/(256*256-1)])
                                    return data
                                data = [process(d) for d in data]
                                print(data)
                        '''
                        f.write(packer_s1.pack(track.buffertype.value))
                        f.write(packer_s1.pack(track.tracktype.value))
                        f.write(packer_s1.pack(track.bonetype))
                        f.write(packer_u1.pack(track.boneid))
                        f.write(packer_f4le.pack(track.weight))

                        f.write(packer_s8le.pack(track.buffersize))

                        f.write(packer_u8le.pack(buffer_table[track_idx]))

                        for rdata in track.referencedata:
                            f.write(packer_f4le.pack(rdata))
                            #assert(rdata == 1.0 or rdata == 0.0)

                        f.write(packer_u8le.pack(extremes_table[track_idx]))

                        track_pointer += 48

                    return result_pointer

            def fill_eventclasses_table():
                nonlocal allocator_pointer
                nonlocal entry
                #eventclassesptr
                if entry.eventclasses is None:
                    return 0
                    #f.write(packer_s8le.pack(0))
                else:
                    #f.write(packer_s8le.pack(allocator_pointer))
                    result_pointer = allocator_pointer
                    f.seek(allocator_pointer)
                    eventclass_pointer = allocator_pointer
                    allocator_pointer += (32*2+8+8)*4
                    #writeeventclasses
                    eventclass : lmt.Lmt.Animevent
                    for eventclass in entry.eventclasses: #type: Lmt.Animevent

                        eventclass_pointer += (32*2+8+8)

                        for remap in eventclass.eventremaps:
                            f.write(packer_s2le.pack(remap))

                        f.write(packer_s8le.pack(eventclass.numevents))
                        if eventclass.numevents == 0:
                            f.write(packer_s8le.pack(0))
                        else:
                            f.write(packer_s8le.pack(allocator_pointer))
                            f.seek(allocator_pointer)
                            allocator_pointer += 8 * eventclass.numevents
                            event : lmt.Lmt.Event
                            for event in eventclass.events:
                                f.write(packer_u4le.pack(event.runeventbit))
                                f.write(packer_u4le.pack(event.numframes))
                            
                            f.seek(eventclass_pointer)

                    return result_pointer

            if entry.flags == 0x800000:
                track_pointer = fill_track_table()
            else:
                #HACK
                track_pointer = entry.trackptr

            #    if first_track_pointer == 0:
            #        first_track_pointer = track_pointer
            #else:
            #    track_pointer = first_track_pointer
            #    print(entry.flags, entry_idx)
            #    eventclasses_pointer = fill_eventclasses_table()
            #    track_pointer = fill_track_table()

            eventclasses_pointer = fill_eventclasses_table()

            f.seek(entry_pointer)
            f.write(packer_s8le.pack(track_pointer))
            f.write(packer_s4le.pack(entry.trackcount))
            f.write(packer_s4le.pack(entry.numframes))
            f.write(packer_s4le.pack(entry.loopframe))
            f.write(packer_s4le.pack(entry.t1))
            f.write(packer_s4le.pack(entry.t2))
            f.write(packer_s4le.pack(entry.t3))
            for endpos in entry.endframeadditivesceneposition:
                f.write(packer_f4le.pack(endpos))
            for endpos in entry.endframeadditivescenerotation:
                f.write(packer_f4le.pack(endpos))
            f.write(packer_s8le.pack(entry.flags))
            f.write(packer_s8le.pack(eventclasses_pointer))

            #floattrackptr
            if entry.floattracksptr == 0:
                f.write(packer_s8le.pack(0))
            else:
                f.write(packer_s8le.pack(allocator_pointer))
                f.seek(allocator_pointer)
                #writefloattrackptr
                #allocator_pointer += size of floattrackptr

                f.seek(entry_pointer+88)

            f.seek(motions_pointer)

class Object(object):
    pass

def gen_track(id, track_type, obj, controller) -> lmt.Lmt.Track:
    numKeys = rt.numKeys(controller)

    track = Object()

    keys = [int(key.time) for key in controller.keys]
    #print('keys',keys)

    # calculate each key difference to prior
    keys = [k1 - k2 for k1, k2 in zip(keys, [0] + keys)]
    #print('keys',keys)

    values = [k.value for k in controller.keys]
    #[rt.getKey(controller,i).value for i in range(1,numKeys+1)]

    if obj.name == 'jnt_2':
        [print('here', v) for v in values]

    keys = keys + [0]
    values = values + values[-1:]

    controllerType = str(controller)

    # position
    if track_type == 0:
        track.tracktype = lmt.Lmt.Track.Tracktype.localposition
        if numKeys <= 1:
            track.buffertype = lmt.Lmt.Track.Compression.singlevector3
            values = values[0:1] #[obj.position]
            keys = keys[0:1]
        else: 
            if controllerType == 'Controller:Linear_Position':
                track.buffertype = lmt.Lmt.Track.Compression.linearvector3
            else:
                track.buffertype = lmt.Lmt.Track.Compression.bilinearvector3_8bit
        #(ds * mt.rotation) + mt.position
        mt = rt.t_pose[id]
        def pos2vec(value):
            if not obj.Parent is None:
                value = value * rt.inverse(obj.Parent.transform)
            if obj.name == 'jnt_2':
                print('mt.rotation', mt.rotation)
                print('mt.position', mt.position)
                print('value', rt.classOf(value), value)
                print(obj.name, (value - mt.position) * rt.inverse(mt.rotation), value)
            value = (value - mt.position) * rt.inverse(mt.rotation)
            return [value.x,value.y,value.z,1.0]

        values = [pos2vec(value) for value in values]

    # rotation
    if track_type == 1:
        track.tracktype = lmt.Lmt.Track.Tracktype.localrotation
        #print(obj.name, numKeys, controllerType)
        if numKeys <= 1:
            track.buffertype = lmt.Lmt.Track.Compression.singlerotationquat3
            values = values[0:1] #values = [obj.rotation]
            keys = keys[0:1]
        else: 
            if controllerType == 'Controller:Linear_Rotation':
                track.buffertype = lmt.Lmt.Track.Compression.linearrotationquat4_14bit
            else:
                track.buffertype = lmt.Lmt.Track.Compression.bilinearrotationquat4_7bit
        def quat2vec(value):
            value = rt.inverse(value) * rt.inverse(rt.t_pose[id].rotation)
            return[value.x,value.y,value.z,-value.w]

        if obj.name == 'jnt_2':
            print('rot[0]', values[0], rt.t_pose[id].rotation)

        values = [quat2vec(value) for value in values]

        if obj.name == 'jnt_2':
            print('rot[0]', values[0], rt.t_pose[id].rotation)

            #for k in values[0]
            #print(obj.name, k) 

    # scale
    if track_type == 2:
        track.tracktype = lmt.Lmt.Track.Tracktype.localscale
        if numKeys <= 1:
            track.buffertype = lmt.Lmt.Track.Compression.singlevector3
            values = values[0:1] #values = [obj.scale]
            keys = keys[0:1]
        else: 
            if controllerType == 'Controller:Linear_Scale':
                track.buffertype = lmt.Lmt.Track.Compression.linearvector3
            else:
                track.buffertype = lmt.Lmt.Track.Compression.bilinearvector3_8bit
        values = [[value.x,value.y,value.z,0.0] for value in values]

    #print(track_type, track.tracktype, track.buffertype, controllerType, values, keys)

    track.bonetype = 0 #self._io.read_u1()
    track.boneid = id #self._io.read_u1()
    track.weight = 1 #self._io.read_f4le()

    track.referencedata = values[0]

    print(obj.name, track.tracktype, keys)

    track.buffer, track.extremes = codec.generate_buffer(track.buffertype, values[1:], keys[1:])

    '''ASSERT '''
    data = [kf for kf in codec.process_buffer(track.buffertype, track.buffer, track.extremes)]

    #[print(i,j) for i,j in zip(values[1:], [d[0] for d in data])]

    #assert(np.linalg.norm(np.subtract(values[1:], [d[0] for d in data])) < 0.001)

    #if obj.name == 'jnt_1':
    #    print(track.buffer)

    if track.buffer is None:
        track.buffersize = 0
    else:
        track.buffersize = len(track.buffer)

    #print(track.buffer, track.extremes)

    return track

class MtMaxAnimationImportExportRollout(MtRollout):
    lmt : lmt.Lmt

    @staticmethod
    def btnFilePressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 animation', 'lmt' )
        if path == None:
            return
        
        MtMaxAnimationImportExportRollout.setFilePath( path )

    @staticmethod
    def edtFileChanged( state ):
        MtMaxAnimationImportExportRollout.setFilePath( state )

    @staticmethod
    def setFilePath( path ):
        mtmaxconfig.animationFilePath = path
        print(mtmaxconfig.animationFilePath)
        #MtMaxModelImportRollout.loadConfig()

    @staticmethod
    def btnLoadPressed():
        try:
            mtmaxlog.clear()
            mtmaxconfig.dump()

            self = MtMaxAnimationImportExportRollout.getMxsVar()
            self.spnAnimationIndex.range = rt.Point3(0,10,5)

            MtMaxAnimationImportExportRollout.lmt = lmt.Lmt.from_file(mtmaxconfig.animationFilePath)
            '''
            types = []

            for e in MtMaxAnimationImportExportRollout.lmt.entries[0:1]:
                if not e.entry is None:
                    anim : lmt.Anim = MtMaxAnimationImportExportRollout.lmt.entries[self.spnAnimationIndex.value].entry
                    for idx, track in enumerate(anim.tracklist):
                        print('boneid', idx, track.boneid)
            '''
            self.spnAnimationIndex.range = rt.Point3(0,MtMaxAnimationImportExportRollout.lmt.entrycount,0)

            return

            #importer = MtModelImporter()
            #importer.importModel( mtmaxconfig.importFilePath )
            if mtmaxlog.hasError():
                mtmaxutil.showErrorMessageBox( "Animation load completed with one or more errors.", '' )
                mtmaxutil.openListener()
            else:
                mtmaxutil.showMessageBox( 'Animation load completed successfully' )
        except Exception as e:
            mtmaxutil._handleException( e, 'A fatal error occured during import.' )

    @staticmethod
    def btnImportPressed():
        try:
            mtmaxlog.clear()
            mtmaxconfig.dump()

            self = MtMaxAnimationImportExportRollout.getMxsVar()

            anim : lmt.Anim = MtMaxAnimationImportExportRollout.lmt.entries[self.spnAnimationIndex.value].entry

            rt.t_pose = [None]*255

            rt.boneids = []

            # clear
            for obj in rt.objects:
                if obj.name.startswith('jnt_'):
                    #print(obj.name, obj.controller.rotation, obj.controller.position)
                    rt.t_pose[int(obj.name.replace('jnt_',''))] = obj.controller
                    obj.controller = rt.prs()

            rt.animationRange = rt.interval(0,1)

            for idx, track in enumerate(anim.tracklist):
                if track.boneid == 255:
                    continue

                obj = rt.getNodeByName(f'jnt_{track.boneid}')

                #print(track.boneid, obj)

                if obj == None:
                    continue

                if (lmt.Lmt.Track.Tracktype.absoluteposition == track.tracktype or \
                    lmt.Lmt.Track.Tracktype.localposition == track.tracktype):
                    if track.buffertype == lmt.Lmt.Track.Compression.singlevector3 or track.buffertype == lmt.Lmt.Track.Compression.linearvector3:
                        obj.controller[0].controller = rt.linear_position()
                    if track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_8bit or track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_16bit:
                        obj.controller[0].controller = rt.bezier_position()

                if (lmt.Lmt.Track.Tracktype.absoluterotation == track.tracktype or \
                    lmt.Lmt.Track.Tracktype.localrotation == track.tracktype):
                    if track.buffertype == lmt.Lmt.Track.Compression.singlerotationquat3 or track.buffertype == lmt.Lmt.Track.Compression.linearrotationquat4_14bit:
                        obj.controller[1].controller = rt.linear_rotation()
                    if track.buffertype == lmt.Lmt.Track.Compression.bilinearrotationquat4_7bit:
                        obj.controller[1].controller = rt.bezier_rotation()

                if (lmt.Lmt.Track.Tracktype.xpto == track.tracktype or \
                    lmt.Lmt.Track.Tracktype.localscale == track.tracktype):
                    if track.buffertype == lmt.Lmt.Track.Compression.singlevector3 or track.buffertype == lmt.Lmt.Track.Compression.linearvector3:
                        obj.controller[2].controller = rt.linear_scale()
                    if track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_8bit or track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_16bit:
                        obj.controller[2].controller = rt.bezier_scale()

            with mx.animate(True):
                for idx, track in enumerate(anim.tracklist):
                    #print('boneid ',track.boneid, track.tracktype, track.buffertype, track.buffersize)
                    if track.boneid == 255:
                        continue

                    obj = rt.getNodeByName(f'jnt_{track.boneid}')

                    #print(track.boneid, obj)

                    if obj == None:
                        print('boneid not found ', track.boneid)
                        continue

                    #rt.addNewKey(obj.controller,0)

                    mt = rt.t_pose[track.boneid]

                    rt.boneids.append(track.boneid)

                    #if lmt.Lmt.Track.Tracktype.localrotation == track.tracktype:
                    #    print(track.boneid, track.tracktype, track.referencedata)

                    if not track.buffer is None:

                        data = [kf for kf in codec.process_buffer(track.buffertype, track.buffer, track.extremes)]

                        data_frames, key_frames = [d[0] for d in data], [d[1] for d in data]
                        num_frames = sum([d[1] for d in data])

                        _buffer, _extremes = codec.generate_buffer(track.buffertype, data_frames, key_frames)

                        '''
                        print('buffertype', track.buffertype)
                        print('extremes original', 'None' if track.extremes is None else (track.extremes.min, track.extremes.max))

                        [ print('data', d) for d in data_frames ]
                        print('extremes', 'None' if track.extremes is None else (track.extremes.min, track.extremes.max))
                        print('extremes', 'None' if _extremes is None else (_extremes.min, _extremes.max))
                        if _extremes is None:
                            assert(not ((_extremes is None) ^ (track.extremes is None)))
                        else:
                            print('extremes', np.abs(np.subtract(_extremes.min,track.extremes.min)))
                            print('extremes', np.abs(np.subtract(_extremes.max,track.extremes.max)))
                            assert((np.abs(np.subtract(_extremes.min,track.extremes.min)) < 0.002).all())
                            assert((np.abs(np.subtract(_extremes.max,track.extremes.max)) < 0.002).all())
                        '''
                    else:
                        data_frames, key_frames = [], []
                        num_frames = 0

                    data_frames = [track.referencedata] + data_frames
                    key_frames = [0] + key_frames

                    '''
                    if (lmt.Lmt.Track.Tracktype.absoluteposition == track.tracktype or \
                        lmt.Lmt.Track.Tracktype.localposition == track.tracktype) and \
                        not mt is None:
                        pass
                        #print(obj.name, track.tracktype, track.buffertype, obj.controller[0].controller, num_frames)

                    if (lmt.Lmt.Track.Tracktype.absoluterotation == track.tracktype or \
                        lmt.Lmt.Track.Tracktype.localrotation == track.tracktype) and \
                        not mt is None:
                        pass
                        #print(obj.name, track.tracktype, track.buffertype, obj.controller[1].controller, num_frames)

                    if (lmt.Lmt.Track.Tracktype.xpto == track.tracktype or \
                        lmt.Lmt.Track.Tracktype.localscale == track.tracktype) and \
                        not mt is None:
                        pass
                        #print(obj.name, track.tracktype, track.buffertype, obj.controller[2].controller, num_frames)
                    '''

                    #if len(data_frames) == 1:
                    if obj.name == 'jnt_2':
                        print(track.boneid, track.tracktype, track.referencedata)

                    print(obj.name, track.buffertype, key_frames)
                    assert(key_frames[-1]==0)
                    #if len(data_frames) >= 2:
                    #    print("data_frames[-2]", data_frames[-2])
                    #    print("data_frames[-1]", data_frames[-1])
                    #    assert(np.linalg.norm(np.subtract(data_frames[-1],data_frames[-2])) < 0.002)
                    
                    """if (lmt.Lmt.Track.Tracktype.absoluteposition == track.tracktype or \
                        lmt.Lmt.Track.Tracktype.localposition == track.tracktype) and \
                        not mt is None:
                        if obj.name == 'jnt_5':
                            print('mt.rotation', mt.rotation)
                            print('mt.position', mt.position)
                            [print(ds, (rt.Point3(float(ds[0]), float(ds[1]), float(ds[2])) * mt.rotation) + mt.position) for ds in data_frames]"""

                    for df_idx, ds in enumerate(data_frames):
                        
                        curr_frame = np.sum(key_frames[0:(df_idx+1)])
                        
                        if int(rt.animationRange.end) < curr_frame:
                            rt.animationRange = rt.interval(0,int(curr_frame))

                        with mx.attime(curr_frame):
                            if (lmt.Lmt.Track.Tracktype.xpto == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localscale == track.tracktype) and \
                                not mt is None:
                                ds = rt.Point3(float(ds[0]), float(ds[1]), float(ds[2]))
                                k = rt.addNewKey(obj.controller[2].controller, int(curr_frame))
                                #k.value = ds

                            if (lmt.Lmt.Track.Tracktype.absoluteposition == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localposition == track.tracktype) and \
                                not mt is None:
                                ds = rt.Point3(float(ds[0]), float(ds[1]), float(ds[2]))
                                k = rt.addNewKey(obj.controller[0].controller, int(curr_frame))
                                #k.value = (ds * mt.rotation) + mt.position
                                #if obj.name == 'jnt_1':
                                #    print(track.buffer)
                                    #print(ds, (ds * mt.rotation) + mt.position, mt.rotation, mt.position)

                            if (lmt.Lmt.Track.Tracktype.absoluterotation == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localrotation == track.tracktype) and \
                                not mt is None:
                                ds = rt.Quat(float(ds[0]), float(ds[1]), float(ds[2]), float(-ds[3]))
                                k = rt.addNewKey(obj.controller[1].controller, int(curr_frame))
                                k.value = rt.inverse(ds * mt.rotation)

                    if (lmt.Lmt.Track.Tracktype.absoluterotation == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localrotation == track.tracktype) and \
                                not mt is None:
                        if obj.name == 'jnt_2':
                            [print(obj.name, k.value) for k in obj.controller[1].controller.keys]

                    '''ASSERTION track.buffer '''
                    '''
                    track_type = [1,0,2][track.tracktype.value%3]
                    print('gen_track', track.boneid, track_type, obj, obj.controller[track_type].controller)
                    track_new = gen_track(track.boneid, track_type, obj, obj.controller[track_type].controller)

                    print('buffertype', track_new.buffertype, track.buffertype)
                    assert(track_new.buffertype.value == track.buffertype.value)
                    print('buffer', track.buffer)
                    print('buffer', track_new.buffer)
                    print('extremes', 'None' if track.extremes is None else (track.extremes.min, track.extremes.max))
                    print('extremes', 'None' if track_new.extremes is None else (track_new.extremes.min, track_new.extremes.max))
                    if track_new.buffer is None:
                        assert(not ((track_new.buffer is None) ^ (track.buffer is None)))
                    else:
                        assert((track_new.buffer == track.buffer).all())
                    if track_new.extremes is None:
                        assert(not ((track_new.extremes is None) ^ (track.extremes is None)))
                    else:
                        assert((track_new.extremes == track.extremes).all())
                    '''

            #importer = MtModelImporter()
            #importer.importModel( mtmaxconfig.importFilePath )
            #if mtmaxlog.hasError():
            #    mtmaxutil.showErrorMessageBox( "Import completed with one or more errors.", '' )
            #    mtmaxutil.openListener()
            #else:
            #    mtmaxutil.showMessageBox( 'Import completed successfully' )
        except Exception as e:
            mtmaxutil._handleException( e, 'A fatal error occured during import.' )

    @staticmethod
    def btnUpdatePressed():
        rt.clearlistener()

        lmt_obj = MtMaxAnimationImportExportRollout.lmt
        self = MtMaxAnimationImportExportRollout.getMxsVar()
        anim : lmt.Lmt.Animentry = lmt_obj.entries[self.spnAnimationIndex.value].entry

            # = self._io.read_s8le()

            #for i in range(1,rt.numKeys(controller[type].controller)+1):
            #    print(rt.getKey(controller[type].controller,i).value)

        def check_obj(obj) -> bool:
            if  rt.numKeys(obj.controller[0].controller) > 0 or \
                rt.numKeys(obj.controller[1].controller) > 0 or \
                rt.numKeys(obj.controller[2].controller) > 0:
                return True
            else:
                return False
                '''
                id = int(obj.Name.replace('jnt_',''))
                mt = rt.t_pose[id]
                print("check_obj",
                    obj.Controller.Position)
                print("check_obj",
                    obj.Controller.Rotation,
                    obj.Controller.Rotation * rt.inverse(mt.rotation))
                print("check_obj",
                    obj.Controller.Scale)
                print(mt.position, mt.rotation, mt.scale)
                '''
            return True

        def gen_tracks(obj) -> List[lmt.Lmt.Track]:
            id = int(obj.Name.replace('jnt_',''))
            #print(obj.name)

            if not check_obj(obj):
                return [None]

            return [gen_track(id,i,obj,obj.controller[i].controller) for i in range(3)]

        tracks = []

        count_objs = 0

        root_obj = rt.getNodeByName('jnt_1')

        def list_objects(obj):
            ret = [obj]
            for child in obj.Children:
                ret += list_objects(child)
            return ret

        for obj in list_objects(root_obj):
            #print(obj.Name)
            for track in gen_tracks(obj):
                if not track is None:
                    count_objs += 1
                    tracks.append(track)
                #else:
                #    print('notrack', obj.name)

        #for idx, track in enumerate(tracks):
        #    print('boneid ',track.boneid, track.tracktype, track.buffertype, track.referencedata)

        root_track_rotation = Object()
        root_track_rotation.tracktype = lmt.Lmt.Track.Tracktype.absoluterotation
        root_track_rotation.buffertype = lmt.Lmt.Track.Compression.singlerotationquat3
        root_track_rotation.bonetype = 0 
        root_track_rotation.boneid = 255
        root_track_rotation.weight = 1
        root_track_rotation.referencedata = [0,0,0,1]
        root_track_rotation.buffer = None
        root_track_rotation.extremes = None
        root_track_rotation.buffersize = 0

        root_track_position = Object()
        root_track_position.tracktype = lmt.Lmt.Track.Tracktype.absoluteposition
        root_track_position.buffertype = lmt.Lmt.Track.Compression.singlevector3
        root_track_position.bonetype = 0 
        root_track_position.boneid = 255
        root_track_position.weight = 1
        root_track_position.referencedata = [0,0,0,1]
        root_track_position.buffer = None
        root_track_position.extremes = None
        root_track_position.buffersize = 0

        root_track_scale = Object()
        root_track_scale.tracktype = lmt.Lmt.Track.Tracktype.xpto
        root_track_scale.buffertype = lmt.Lmt.Track.Compression.singlevector3
        root_track_scale.bonetype = 0 
        root_track_scale.boneid = 255
        root_track_scale.weight = 1
        root_track_scale.referencedata = [1,1,1,0]
        root_track_scale.buffer = None
        root_track_scale.extremes = None
        root_track_scale.buffersize = 0

        root_tracks = [root_track_rotation, root_track_position, root_track_scale]

        anim._m_tracklist = root_tracks + tracks
        print(count_objs, anim.tracklist)
        anim.trackcount = len(anim.tracklist)

        with open(mtmaxconfig.animationFilePath + ".new", "wb") as f:
            write_lmt(lmt_obj, f)
            print(mtmaxconfig.animationFilePath + ".new")

    @staticmethod
    def updateVisibility():
        rt.MtMaxModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxconfig.importFilePath )
            
    @staticmethod
    def loadConfig():
        self = MtMaxAnimationImportExportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.importFilePath
        MtMaxAnimationImportExportRollout.updateVisibility()