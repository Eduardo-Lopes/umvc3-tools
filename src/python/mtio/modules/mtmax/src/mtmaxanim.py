import os
import mtmaxconfig, mtmaxutil
from pymxs import runtime as rt
import pymxs as mx

from mtmaxrollout import MtRollout

import mtmaxlog
import lmt
import codec
import numpy as np

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

            self.spnAnimationIndex.range = rt.Point3(0,MtMaxAnimationImportExportRollout.lmt.entrycount,0)

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

            mts = [None]*len(anim.tracklist)

            # clear
            for obj in rt.objects:
                if obj.name.startswith('jnt_'):
                    obj.controller = rt.prs()

            for idx, track in enumerate(anim.tracklist):
                if track.boneid == 255:
                    continue

                obj = rt.getNodeByName(f'jnt_{track.boneid}')

                #print(track.boneid, obj)

                if obj == None:
                    continue

                mts[track.boneid] = obj.controller.rotation

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
                    print(obj.name, track.buffertype, obj.controller[1].controller)

                if (lmt.Lmt.Track.Tracktype.xpto == track.tracktype or \
                    lmt.Lmt.Track.Tracktype.localscale == track.tracktype):
                    if track.buffertype == lmt.Lmt.Track.Compression.singlevector3 or track.buffertype == lmt.Lmt.Track.Compression.linearvector3:
                        obj.controller[2].controller = rt.linear_scale()
                    if track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_8bit or track.buffertype == lmt.Lmt.Track.Compression.bilinearvector3_16bit:
                        obj.controller[2].controller = rt.bezier_scale()


            with mx.animate(True):
                for idx, track in enumerate(anim.tracklist):
                    if track.boneid == 255:
                        continue

                    obj = rt.getNodeByName(f'jnt_{track.boneid}')

                    print(track.boneid, obj)

                    if obj == None:
                        continue

                    rt.addNewKey(obj.controller,0)

                    mt = mts[track.boneid]

                    if not track.buffer is None:

                        data = [kf for kf in codec.process_buffer(track.buffertype, track.buffer, track.extremes)]

                        data_frames, key_frames = [d[0] for d in data], [d[1] for d in data]
                        num_frames = sum([d[1] for d in data])
                    else:
                        data_frames, key_frames = [], []
                        num_frames = 0

                    data_frames = [track.referencedata] + data_frames
                    key_frames = [0] + key_frames
                    
                    for df_idx, ds in enumerate(data_frames):
                        
                        curr_frame = np.sum(key_frames[0:(df_idx+1)])
                        
                        if int(rt.animationRange.end) < curr_frame:
                            rt.animationRange = rt.interval(0,int(curr_frame))

                        with mx.attime(curr_frame):
                            if (lmt.Lmt.Track.Tracktype.xpto == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localscale == track.tracktype) and \
                                not mt is None:
                                ds = rt.Point3(float(ds[0]), float(ds[1]), float(ds[2]))
                                rt.addNewKey(obj.controller, int(curr_frame))
                                obj.controller.Scale = ds

                            if (lmt.Lmt.Track.Tracktype.absoluteposition == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localposition == track.tracktype) and \
                                not mt is None:
                                ds = rt.Point3(float(ds[0]), float(ds[1]), float(ds[2]))
                                rt.addNewKey(obj.controller, int(curr_frame))
                                obj.controller.Pos = ds

                            if (lmt.Lmt.Track.Tracktype.absoluterotation == track.tracktype or \
                                lmt.Lmt.Track.Tracktype.localrotation == track.tracktype) and \
                                not mt is None:
                                ds = rt.Quat(float(ds[0]), float(ds[1]), float(ds[2]), float(-ds[3]))
                                rt.addNewKey(obj.controller, int(curr_frame))
                                obj.controller.Rotation = ds * mt

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
    def btnExportPressed():
        mtmaxlog.debug('btnExportPressed')

    @staticmethod
    def updateVisibility():
        rt.MtMaxModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxconfig.importFilePath )
            
    @staticmethod
    def loadConfig():
        self = MtMaxAnimationImportExportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.importFilePath
        MtMaxAnimationImportExportRollout.updateVisibility()