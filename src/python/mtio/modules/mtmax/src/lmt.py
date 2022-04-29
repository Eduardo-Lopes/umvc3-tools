# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Lmt(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x4C\x4D\x54\x00":
            raise kaitaistruct.ValidationNotEqualError(b"\x4C\x4D\x54\x00", self.magic, self._io, u"/seq/0")
        self.version = self._io.read_u2le()
        self.entrycount = self._io.read_u2le()
        self.entries = [None] * (self.entrycount)
        for i in range(self.entrycount):
            self.entries[i] = Lmt.Motion(self._io, self, self._root)


    class Event(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.runeventbit = self._io.read_u4le()
            self.numframes = self._io.read_u4le()


    class Track(KaitaiStruct):

        class Compression(Enum):
            singlevector3 = 1
            singlerotationquat3 = 2
            linearvector3 = 3
            bilinearvector3_16bit = 4
            bilinearvector3_8bit = 5
            linearrotationquat4_14bit = 6
            bilinearrotationquat4_7bit = 7
            bilinearrotationquatxw_14bit = 11
            bilinearrotationquatyw_14bit = 12
            bilinearrotationquatzw_14bit = 13
            bilinearrotationquat4_11bit = 14
            bilinearrotationquat4_9bit = 15

        class Tracktype(Enum):
            localrotation = 0
            localposition = 1
            localscale = 2
            absoluterotation = 3
            absoluteposition = 4
            xpto = 5
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.buffertype = KaitaiStream.resolve_enum(Lmt.Track.Compression, self._io.read_s1())
            self.tracktype = KaitaiStream.resolve_enum(Lmt.Track.Tracktype, self._io.read_s1())
            self.bonetype = self._io.read_u1()
            self.boneid = self._io.read_u1()
            self.weight = self._io.read_f4le()
            self.buffersize = self._io.read_s8le()
            self.bufferptr = self._io.read_s8le()
            self.referencedata = [None] * (4)
            for i in range(4):
                self.referencedata[i] = self._io.read_f4le()

            self.extremesptr = self._io.read_s8le()

        @property
        def buffer(self):
            if hasattr(self, '_m_buffer'):
                return self._m_buffer if hasattr(self, '_m_buffer') else None

            if self.bufferptr != 0:
                io = self._root._io
                _pos = io.pos()
                io.seek(self.bufferptr)
                self._m_buffer = [None] * (self.buffersize)
                for i in range(self.buffersize):
                    self._m_buffer[i] = io.read_u1()

                io.seek(_pos)

            return self._m_buffer if hasattr(self, '_m_buffer') else None

        @property
        def extremes(self):
            if hasattr(self, '_m_extremes'):
                return self._m_extremes if hasattr(self, '_m_extremes') else None

            if self.extremesptr != 0:
                io = self._root._io
                _pos = io.pos()
                io.seek(self.extremesptr)
                self._m_extremes = Lmt.Extreme(io, self, self._root)
                io.seek(_pos)

            return self._m_extremes if hasattr(self, '_m_extremes') else None


    class Motion(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.dataoffset = self._io.read_u8le()

        @property
        def entry(self):
            if hasattr(self, '_m_entry'):
                return self._m_entry if hasattr(self, '_m_entry') else None

            if self.dataoffset != 0:
                io = self._root._io
                _pos = io.pos()
                io.seek(self.dataoffset)
                self._m_entry = Lmt.Animentry(io, self, self._root)
                io.seek(_pos)

            return self._m_entry if hasattr(self, '_m_entry') else None


    class Animentry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.trackptr = self._io.read_u8le()
            self.trackcount = self._io.read_s4le()
            self.numframes = self._io.read_s4le()
            self.loopframe = self._io.read_s4le()
            self.t1 = self._io.read_s4le()
            if not self.t1 == 0:
                raise kaitaistruct.ValidationNotEqualError(0, self.t1, self._io, u"/types/animentry/seq/4")
            self.t2 = self._io.read_s4le()
            if not self.t2 == 0:
                raise kaitaistruct.ValidationNotEqualError(0, self.t2, self._io, u"/types/animentry/seq/5")
            self.t3 = self._io.read_s4le()
            if not self.t3 == 0:
                raise kaitaistruct.ValidationNotEqualError(0, self.t3, self._io, u"/types/animentry/seq/6")
            self.endframeadditivesceneposition = [None] * (4)
            for i in range(4):
                self.endframeadditivesceneposition[i] = self._io.read_f4le()

            self.endframeadditivescenerotation = [None] * (4)
            for i in range(4):
                self.endframeadditivescenerotation[i] = self._io.read_f4le()

            self.flags = self._io.read_s8le()
            self.eventclassesptr = self._io.read_s8le()
            self.floattracksptr = self._io.read_s8le()

        @property
        def tracklist(self):
            if hasattr(self, '_m_tracklist'):
                return self._m_tracklist if hasattr(self, '_m_tracklist') else None

            io = self._root._io
            _pos = io.pos()
            io.seek(self.trackptr)
            self._m_tracklist = [None] * (self.trackcount)
            for i in range(self.trackcount):
                self._m_tracklist[i] = Lmt.Track(io, self, self._root)

            io.seek(_pos)
            return self._m_tracklist if hasattr(self, '_m_tracklist') else None

        @property
        def eventclasses(self):
            if hasattr(self, '_m_eventclasses'):
                return self._m_eventclasses if hasattr(self, '_m_eventclasses') else None

            io = self._root._io
            _pos = io.pos()
            io.seek(self.eventclassesptr)
            self._m_eventclasses = [None] * (4)
            for i in range(4):
                self._m_eventclasses[i] = Lmt.Animevent(io, self, self._root)

            io.seek(_pos)
            return self._m_eventclasses if hasattr(self, '_m_eventclasses') else None


    class Animevent(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.eventremaps = [None] * (32)
            for i in range(32):
                self.eventremaps[i] = self._io.read_s2le()

            self.numevents = self._io.read_u8le()
            self.eventsptr = self._io.read_u8le()

        @property
        def events(self):
            if hasattr(self, '_m_events'):
                return self._m_events if hasattr(self, '_m_events') else None

            io = self._root._io
            _pos = io.pos()
            io.seek(self.eventsptr)
            self._m_events = [None] * (self.numevents)
            for i in range(self.numevents):
                self._m_events[i] = Lmt.Event(io, self, self._root)

            io.seek(_pos)
            return self._m_events if hasattr(self, '_m_events') else None


    class Extreme(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.min = [None] * (4)
            for i in range(4):
                self.min[i] = self._io.read_f4le()

            self.max = [None] * (4)
            for i in range(4):
                self.max[i] = self._io.read_f4le()




