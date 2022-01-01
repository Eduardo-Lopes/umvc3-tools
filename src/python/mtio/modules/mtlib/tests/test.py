import os
import sys
import io

sys.path.append( os.path.dirname( sys.path[0] ) )
sys.path.append( os.path.dirname( os.path.dirname( sys.path[0] ) ) )

from ncl import *
from immaterial import *
from rmaterial import *
from rmodel import * 
import mvc3materialdb
import mvc3shaderdb
import util
from rtexture import *

def areBuffersEqual( a, b ):
    if len( a ) != len( b ): return False
    for i in range( len( a ) ):
        if a[i] != b[i]: 
            return False
    return True

def testMrlYaml( mrlBuffer, modPath ):
    # read model for material names
    mod = rModelData()
    mod.read( NclBitStream( util.loadIntoByteArray( modPath ) ) )
    mvc3materialdb.addNames( mod.materials )
    
    # read mtl into intermediate 
    imMrl = imMaterialLib()
    imMrl.loadBinary( NclBitStream( mrlBuffer ) )
    
    # write to binary and compare
    stream = NclBitStream()
    imMrl.saveBinary( stream )
    imMrlBuf = stream.getBuffer()
    if not areBuffersEqual( mrlBuffer, imMrlBuf ):
        # write original mtl for comparison
        with open( "test_original.mrl", "wb" ) as f:
            f.write( mrlBuffer )
        
        with open( "test_yaml.mrl", "wb") as f:
            f.write( imMrlBuf )
            assert( False )
        
    # save to yml
    yamlFile = io.StringIO()
    imMrl.saveYamlIO( yamlFile )
    
    # load from yml, write and compare
    yamlFile.seek( 0 )
    imMrl.loadYamlIO( yamlFile )
    
    stream = NclBitStream()
    imMrl.saveBinary( stream )
    imMrlBuf = stream.getBuffer()
    if not areBuffersEqual( mrlBuffer, imMrlBuf ):
        with open( "test.mrl", "wb" ) as f:
            f.write( imMrlBuf )
            assert( False )
        
def dumpMaterialNames():
    names = set()
    with os.scandir('X:\\work\\umvc3_model\\samples\\test') as it:
        for entry in it:
            if entry.name.endswith(".mod") and entry.is_file():
                print( entry.name )
                reader = rModelStreamReader( NclBitStream( util.loadIntoByteArray( entry.path ) ) )
                for mat in reader.iterMaterials():
                    names.add( mat )
        
    with open( "materialnames.txt", "w" ) as f:            
        for name in names:
            f.write( name + "\n" )

def testMrl( inputName, ignoreAnim ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    # read mtl
    mrl = rMaterialData()
    mrlBuffer = util.loadIntoByteArray( mrlPath )
    mrl.read(NclBitStream( mrlBuffer ) )
    
    hasAnimData = False
    for mat in mrl.materials:
        if mat.animData != None:
            hasAnimData = True
            break
        
    if ignoreAnim and hasAnimData:
        print( "ignored: {}".format( inputName ) )
        return
    
    # write mtl and compare output
    stream = NclBitStream()
    mrl.write( stream )
    mrlNewBuffer = stream.getBuffer()
    if not areBuffersEqual( mrlBuffer, mrlNewBuffer ):
        # write original mtl for comparison
        with open( "test_original.mrl", "wb" ) as f:
            f.write( mrlBuffer )
            
        with open( "test.mrl", "wb" ) as f:
            f.write( mrlNewBuffer )
            
        assert( False )
        
    testMrlYaml( mrlBuffer, modPath )
    print( "passed: {}".format( inputName ) )
    
def processMrlBatch( func, *args ):
    with os.scandir('X:\\work\\umvc3_model\\samples\\test') as it:
        for entry in it:
            if entry.name.endswith(".mrl") and entry.is_file():
                func( entry.path, *args )

def testMod( inputName ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    # read mod
    modBuffer = util.loadIntoByteArray( modPath )
    mod = rModelData()
    mod.read( NclBitStream( modBuffer ) )

    # write mod and compare output
    stream = NclBitStream()
    mod.write( stream )
    modNewBuffer = stream.getBuffer()
    if not areBuffersEqual( modBuffer, modNewBuffer ):
        # write original mod for comparison
        with open( "test_original.mod", "wb" ) as f:
            f.write( modBuffer )
            
        with open( "test.mod", "wb" ) as f:
            f.write( modNewBuffer )
            
        assert( False )
    
    print( "passed: {}".format( inputName ) )
    
def addFreq( stats, key, val ):
    if not key in stats:
        stats[key] = dict()

    if not val in stats[key]:
        stats[key][val] = 1
    else:
        stats[key][val] += 1
        
def addUnique( stats, key, val ):
    if not key in stats:
        stats[key] = dict()

    if not val in stats[key]:
        stats[key].append( val )
        
def addUnique2( stats, key, a, b ):
    if not key in stats:
        stats[key] = dict()
        
    if not a in stats[key]:
        stats[key][a] = list()

    if not b in stats[key][a]:
        stats[key][a].append( b )
    
def dumpModStats( inputName, stats ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    # read mod
    modBuffer = util.loadIntoByteArray( modPath )
    mod = rModelData()
    mod.read( NclBitStream( modBuffer ) )
    
    addFreq( stats, 'header.vertexBuffer2Size', mod.header.vertexBuffer2Size )   
    addFreq( stats, 'header.exData present', mod.exData != None ) 
    addFreq( stats, 'header.field90', mod.header.field90 )
    addFreq( stats, 'header.field94', mod.header.field94 )
    addFreq( stats, 'header.field98', mod.header.field98 )
    addFreq( stats, 'header.field9c', mod.header.field9c )
        
    for prim in mod.primitives:
        addFreq( stats, 'prim.type', prim.type )
        addFreq( stats, 'prim.lod', prim.indices.getLodIndex() )
        addFreq( stats, 'prim.flags', prim.flags )
        addFreq( stats, 'prim.flags2', prim.flags2 )
        addFreq( stats, 'prim.renderMode', prim.renderMode )
        addFreq( stats, 'prim.vertexShader', mvc3shaderdb.shaderObjectsByHash[ prim.vertexShader.getHash() ].name )
        addFreq( stats, 'prim.field2c', prim.field2c )
    
    for grp in mod.groups:
        addFreq( stats, "grp.field00", grp.field00 )
        addFreq( stats, "grp.field04", grp.field04 )
        addFreq( stats, "grp.field08", grp.field08 )
        addFreq( stats, "grp.field0c", grp.field0c )
        #addFreq( stats, "grp.field10", grp.field10 )
        
    for joint in mod.joints:
        addFreq( stats, "joint.field03", joint.field03 )
        #addFreq( stats, "joint.field04", joint.field04 )
        #addFreq( stats, "joint.length", joint.length )
        
    for link in mod.primitiveJointLinks:
        addFreq( stats, "link.field04", link.field04 )
        addFreq( stats, "link.field08", link.field08 )
        addFreq( stats, "link.field0c", link.field0c )  
                
def genMetadata( inputName, ref ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    
    # read mod
    modBuffer = util.loadIntoByteArray( modPath )
    mod = rModelData()
    mod.read( NclBitStream( modBuffer ) )
    
    if len( mod.joints ) > 0:
        # try to load the existing metadata if we have it
        filePath = util.getResourceDir() + '/metadata/' + baseName + ".yml"
        metadata = ModelMetadata()
        if os.path.exists( filePath ):
            metadata.loadFile( filePath )  
    
def processModBatch( func, *args ):
    with os.scandir('X:\\work\\umvc3_model\\samples\\test') as it:
        for entry in it:
            if entry.name.endswith(".mod") and entry.is_file():
                func( entry.path, *args )
                
def processTexBatch( func, *args ):
    with os.scandir('X:\\work\\umvc3_model\\samples\\test') as it:
        for entry in it:
            if entry.name.endswith(".tex") and entry.is_file():
                func( entry.path, *args )
                
def logMrlWithAnim( inputName, f ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    # read mtl
    mrl = rMaterialData()
    mrlBuffer = util.loadIntoByteArray( mrlPath )
    mrl.read(NclBitStream( mrlBuffer ) )
    
    hasAnimData = False
    for mat in mrl.materials:
        if mat.animData != None:
            hasAnimData = True
            break
        
    if hasAnimData:
        f.write(baseName + "\n")  
        
class JointStats:
    def __init__( self, id, parentId, symmetryId, uses, usedByFiles ):
        self.id = id
        self.parentId = parentId
        self.symmetryId = symmetryId
        self.uses = uses
        self.usedByFiles = usedByFiles
        
    def __repr__(self) -> str:
        return "id {:3d} parent {:3d} sym {:3d} uses {:3d} usedBy {}".format( self.id, self.parentId, self.symmetryId, self.uses, self.usedByFiles )
        
def findSimilarJoints( inputName, stats ):
    basePath, baseName, exts = util.splitPath( inputName )
    modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
    mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
    ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    # read mod
    modBuffer = util.loadIntoByteArray( modPath )
    mod = rModelData()
    mod.read( NclBitStream( modBuffer ) )
    
    if len( mod.joints ) > 0:
        for modJoint in mod.joints:     
            parentId = -1
            if modJoint.parentIndex not in [-1, 255]:
                parentId = mod.joints[ modJoint.parentIndex ].id
            symmetryId = -1
            if modJoint.symmetryIndex not in [-1, 255]:
                symmetryId = mod.joints[ modJoint.symmetryIndex ].id
            
            found = False
            for statJoint in stats:    
                if statJoint.id == modJoint.id and statJoint.parentId == parentId and statJoint.symmetryId == symmetryId:
                    statJoint.uses += 1
                    statJoint.usedByFiles.append( baseName )
                    found = True
                    break
                
            if not found:
                stats.append( JointStats( modJoint.id, parentId, symmetryId, 1, [ baseName ] ) )
                    
    
    
def testTex( inputPath ):
    try:
        texBuffer = util.loadIntoByteArray( inputPath )
        if len( texBuffer ) == 0 or texBuffer[0] == 0:
            # skip invalid files
            return
        
        tex = rTextureData()
        stream = NclBitStream( texBuffer )
        tex.read( stream )
        assert( tex.header.desc.field2 == 0 )
        assert( tex.header.desc.shift == 0 )
        assert( tex.header.fmt.field3 == 1 )
        assert( tex.header.fmt.field4 == 0 )
        
        # test if saving outputs matching binary
        stream = NclBitStream()
        tex.write( stream )
        newTexBuffer = stream.getBuffer()  
        assert( areBuffersEqual( texBuffer, newTexBuffer ) )
    except Exception as e:
        print( inputPath + '\t' + str( e ) )
        util.saveByteArrayToFile( 'test_orig.tex', texBuffer )
        util.saveByteArrayToFile( 'test.tex', newTexBuffer )
        
def dumpTexFormatInfo( inputPath, list ):
    baseName = os.path.basename( inputPath ).split('.')[0]
    tex = rTextureData()
    tex.loadBinaryFile( inputPath )
    print( baseName + ' ' + str( tex.header.fmt.surfaceFmt ) )
    list.append( ( baseName, tex.header.fmt.surfaceFmt  ) )
    
def dumpSimilarJoints():
    stats = []
    processModBatch( findSimilarJoints, stats )
    for jointStats in sorted( stats, key=lambda k: k.id ):
        if jointStats.uses > 1:
            print(jointStats)
            
def dumpJointInfo():
    jointInfoDb = JointInfoDb()
    jointInfoDb.loadCsvFromFile( JointInfoDb.getDefaultCsvPath( 'Ryu' ) )
    
    processModBatch( genJointInfoCsv, jointInfoDb )
    
def main():
    inputName = "X:/work/umvc3_model/samples/UMVC3ModelSamples/Ryu/Ryu.58a15856.mod"
    baseName = os.path.basename(inputName).split('.')[0]
    basePath = os.path.dirname(inputName)
    data = util.loadIntoByteArray( inputName )
    
    processModBatch( testMod )
    
    # if not os.path.exists("dump/mrl_with_anims.txt"):
    #     with open("dump/mrl_with_anims.txt", "w") as f:
    #         processMrlBatch( logMrlWithAnim, f )
            
    # test textures
    #processTexBatch( testTex ) # passed
    #if not os.path.exists("dump/tex_info.tsv"):
    # info = []
    # processTexBatch( dumpTexFormatInfo, info )
    # info = sorted( info, key=lambda i: i[1])
    
    # with open("dump/tex_info.tsv", "w") as f:
    #     for i in info:
    #         f.write( str(i[1]) + ' ' + str(i[0]) + '\n')
            
    
    #testTex( 'X:/work/umvc3_model/samples/test/Environment_CM.241f5deb.tex' )
    
    #testMod( inputName )
    #testMrl( inputName )
    #processModBatch( testMod )
    
    #processMrlBatch( testMrl, True )
    
    #
    
    #stats = dict()
    #processModBatch( dumpModStats, stats )
    #print(stats)
    
    dumpJointInfo()


if __name__ == '__main__':
    main()