# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 28, 2018

import struct
from mathutils import Vector
from mathutils import Euler


class SparkError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SparkReader:
    def __init__(self, data):
        self.data = data
        self.idx = 0
    
    def getRemainingCount(self):
        return len(self.data) - self.idx
    
    def hasCountRemaining(self, byteCount):
        return self.getRemainingCount() >= byteCount
    
    def doneReading(self):
        return self.getRemainingCount() <= 0
    
    def readData(self, byteCount):
        if not self.hasCountRemaining(byteCount):
            raise SparkError("Unexpected end of data stream.")
        self.idx += byteCount
        return self.data[self.idx-byteCount:self.idx]
    
    def readUInt32(self):
        return struct.unpack("<I", self.readData(4))[0]
    
    def readUInt16(self):
        return struct.unpack("<H", self.readData(2))[0]
    
    def readUInt8(self):
        return self.readData(1)
    
    def readFloat(self):
        return struct.unpack("<f", self.readData(4))[0]
    
    def readVec2(self):
        return struct.unpack("<ff", self.readData(8))
    
    def readVec3(self):
        return struct.unpack("<fff", self.readData(12))
    
    def readString(self):
        byteCount = self.readUInt32()
        return self.readData(byteCount).decode()
    
    def readWString(self):
        stringLength = self.readUInt32()
        return self.readData(stringLength*2).decode('utf-16')
    
    def readChunk(self):
        chunkIdx = self.readUInt32()
        chunkLength = self.readUInt32()
        chunkData = self.readData(chunkLength)
        return chunkIdx, chunkLength, chunkData
    
    def skip(self, byteCount):
        self.readData(byteCount)


class SparkWriter:
    def __init__(self):
        self.data = [b'']
    
    def writeUInt32(self, value):
        self.data[-1] += struct.pack("<I", value)
    
    def writeUInt16(self, value):
        self.data[-1] += struct.pack("<H", value)
    
    def writeUInt8(self, value):
        self.data[-1] += struct.pack("<B", value)
    
    def writeFloat(self, value):
        self.data[-1] += struct.pack("<f", value)
    
    def writeString(self, s):
        self.writeUInt32(len(s))
        self.data[-1] += s.encode()
    
    def writeBytes(self, byteString):
        self.data[-1] += byteString
    
    def beginChunk(self, idx):
        self.writeUInt32(idx)
        self.data.append(b'')
    
    def endChunk(self):
        if len(self.data) <= 1:
            raise SparkError("Attempt to call SparkWriter.endChunk with no in-progress chunks!")
        chunkData = self.data.pop()
        self.writeUInt32(len(chunkData))
        self.writeBytes(chunkData)
    
    def getData(self):
        if len(self.data) > 1:
            raise SparkError("Attempt to call SparkWriter.getData with un-finished chunks!")
        return self.data[0]


class SparkGeoMaterialChunk:
    def readData(self, data):
        self.materials = []
        
        reader = SparkReader(data)
        materialCount = reader.readUInt32()
        for i in range(materialCount):
            self.materials.append(reader.readString())
        return self
    
    def writeData(self, writer):
        writer.beginChunk(4)
        
        writer.writeUInt32(len(self.materials))
        for m in self.materials:
            writer.writeString(m)
        
        writer.endChunk()


class SparkGeoVertex:
    def readData(self, reader):
        self.x = reader.readFloat()
        self.y = reader.readFloat()
        self.z = reader.readFloat()
        reader.skip(1) # extra unused byte at the end of each vertex
        return self
    
    def writeData(self, writer):
        writer.writeFloat(self.x)
        writer.writeFloat(self.y)
        writer.writeFloat(self.z)
        writer.writeUInt8(0)


class SparkGeoVertexChunk:
    def readData(self, data):
        self.vertices = []
        
        reader = SparkReader(data)
        vertexCount = reader.readUInt32()
        for i in range(vertexCount):
            self.vertices.append(SparkGeoVertex().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.beginChunk(1)
        
        writer.writeUInt32(len(self.vertices))
        for v in self.vertices:
            v.writeData(writer)
        
        writer.endChunk()


class SparkGeoEdge:
    def readData(self, reader):
        self.idxA = reader.readUInt32()
        self.idxB = reader.readUInt32()
        self.smooth = True if reader.readUInt8() == 1 else False
        return self
    
    def writeData(self, writer):
        writer.writeUInt32(self.idxA)
        writer.writeUInt32(self.idxB)
        writer.writeUInt8(1 if self.smooth else 0)


class SparkGeoEdgeChunk:
    def readData(self, data):
        self.edges = []
        
        reader = SparkReader(data)
        edgeCount = reader.readUInt32()
        for i in range(edgeCount):
            self.edges.append(SparkGeoEdge().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.beginChunk(2)
        
        writer.writeUInt32(len(self.edges))
        for e in self.edges:
            e.writeData(writer)
        
        writer.endChunk()


class SparkGeoEdgeLoopMember:
    def readData(self, reader):
        self.flipped = True if reader.readUInt32() == 1 else False
        self.edgeIdx = reader.readUInt32()
        return self
    
    def writeData(self, writer):
        writer.writeUInt32(1 if self.flipped else 0)
        writer.writeUInt32(self.edgeIdx)


class SparkGeoEdgeLoop:
    def readData(self, reader):
        edgeCount = reader.readUInt32()
        self.edgeLoopMembers = []
        for i in range(edgeCount):
            self.edgeLoopMembers.append(SparkGeoEdgeLoopMember().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.writeUInt32(len(self.edgeLoopMembers))
        for elm in self.edgeLoopMembers:
            elm.writeData(writer)


class SparkGeoFace:
    def readData(self, reader):
        self.angle = reader.readFloat()
        self.xOffset = reader.readFloat()
        self.yOffset = reader.readFloat()
        self.xScale = reader.readFloat()
        self.yScale = reader.readFloat()
        self.mappingIdx = reader.readUInt32()
        self.materialIdx = reader.readUInt32()
        innerLoopCount = reader.readUInt32()
        self.borderLoop = SparkGeoEdgeLoop().readData(reader)
        self.innerLoops = []
        for i in range(innerLoopCount):
            self.innerLoops.append(SparkGeoEdgeLoop().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.writeFloat(self.angle)
        writer.writeFloat(self.xOffset)
        writer.writeFloat(self.yOffset)
        writer.writeFloat(self.xScale)
        writer.writeFloat(self.yScale)
        writer.writeUInt32(0xFFFFFFFF)
        writer.writeUInt32(self.materialIdx)
        writer.writeUInt32(len(self.innerLoops))
        self.borderLoop.writeData(writer)
        for innerLoop in self.innerLoops:
            innerLoop.writeData(writer)


class SparkGeoFaceChunk:
    def readData(self, data):
        self.faces = []
        
        reader = SparkReader(data)
        faceCount = reader.readUInt32()
        for i in range(faceCount):
            self.faces.append(SparkGeoFace().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.beginChunk(3)
        
        writer.writeUInt32(len(self.faces))
        for f in self.faces:
            f.writeData(writer)
        
        writer.endChunk()


class SparkGeoMappingGroup:
    def readData(self, reader):
        self.id = reader.readUInt32()
        self.angle = reader.readFloat()
        self.xScale = reader.readFloat()
        self.yScale = reader.readFloat()
        self.xOffset = reader.readFloat()
        self.yOffset = reader.readFloat()
        self.xNormal = reader.readFloat()
        self.yNormal = reader.readFloat()
        self.zNormal = reader.readFloat()
        return self
    
    def writeData(self, writer):
        writer.writeUInt32(self.id)
        writer.writeFloat(self.angle)
        writer.writeFloat(self.xScale)
        writer.writeFloat(self.yScale)
        writer.writeFloat(self.xOffset)
        writer.writeFloat(self.yOffset)
        writer.writeFloat(self.xNormal)
        writer.writeFloat(self.yNormal)
        writer.writeFloat(self.zNormal)


class SparkGeoMappingGroupChunk:
    def readData(self, data):
        self.mappingGroups = []
        
        reader = SparkReader(data)
        groupCount = reader.readUInt32()
        for i in range(groupCount):
            self.mappingGroups.append(SparkGeoMappingGroup().readData(reader))
        return self
    
    def writeData(self, writer):
        writer.beginChunk(5)
        
        writer.writeUInt32(len(self.mappingGroups))
        for g in self.mappingGroups:
            g.writeData(writer)
        
        writer.endChunk()
    
    def getMappingById(self, id):
        for i, mapping in enumerate(self.mappingGroups):
            if mapping.id == id:
                return i
        return -1


class SparkGeoData:
    def readData(self, data):
        self.materialChunk = None
        self.vertexChunk = None
        self.edgeChunk = None
        self.faceChunk = None
        self.mappingChunk = None
        
        reader = SparkReader(data)
        chunkIdx, chunkLength, chunkData = reader.readChunk()
        if chunkIdx != 1:
            raise SparkError("Data in clipboard doesn't appear to be valid (header dword not 1)")
        
        # We only care about the mesh chunk.  Start reading THAT chunk's contents.  If it exists,
        # it will be the first chunk.
        reader = SparkReader(chunkData)
        
        if reader.readUInt16() != 2:
            return # no geometry in the clipboard data
        
        while not reader.doneReading():
            
            chunkIdx, chunkLength, chunkData = reader.readChunk()
            
            if chunkIdx == 4:
                if self.materialChunk != None:
                    raise SparkError("Multiple material chunks present in clipboard geo data!")
                self.materialChunk = SparkGeoMaterialChunk().readData(chunkData)
            elif chunkIdx == 1:
                if self.vertexChunk != None:
                    raise SparkError("Multiple vertex chunks present in clipboard geo data!")
                self.vertexChunk = SparkGeoVertexChunk().readData(chunkData)
            elif chunkIdx == 2:
                if self.edgeChunk != None:
                    raise SparkError("Multiple edge chunks present in clipboard geo data!")
                self.edgeChunk = SparkGeoEdgeChunk().readData(chunkData)
            elif chunkIdx == 3:
                if self.faceChunk != None:
                    raise SparkError("Multiple face chunks present in clipboard geo data!")
                self.faceChunk = SparkGeoFaceChunk().readData(chunkData)
            elif chunkIdx == 7:
                if self.mappingChunk != None:
                    raise SparkError("Multiple mapping chunks present in clipboard geo data!")
                self.mappingChunk = SparkGeoMappingGroupChunk().readData(chunkData)
        return self
    
    def writeData(self, writer):
        writer.beginChunk(1)
        writer.writeUInt16(2) # mesh selection manager index
        
        self.materialChunk.writeData(writer)
        self.vertexChunk.writeData(writer)
        self.edgeChunk.writeData(writer)
        self.faceChunk.writeData(writer)
        
        # Fill in blank data for face layers
        writer.beginChunk(6)
        writer.writeUInt32(len(self.faceChunk.faces))
        writer.writeUInt32(2)
        for i in range(len(self.faceChunk.faces)):
            writer.writeUInt32(0)
        writer.endChunk()
        
        self.mappingChunk.writeData(writer)
        
        # Fill in blank data for geometry groups
        writer.beginChunk(8)
        writer.writeUInt32(0) # 0 vert groups
        writer.writeUInt32(0) # 0 edge groups
        writer.writeUInt32(0) # 0 face groups
        writer.endChunk()
        
        writer.endChunk()


class SparkVertex:
    def readData(self, reader):
        self.pos = Vector(reader.readVec3())
        self.nrm = Vector(reader.readVec3())
        self.tan = Vector(reader.readVec3())
        self.bit = Vector(reader.readVec3())
        self.uv = Vector(reader.readVec2())
        reader.readUInt32() # skip color
        reader.skip(32) # skip bone weights and bone indices.
        return self


class SparkFaceSet:
    def readData(self, reader):
        self.materialIndex = reader.readUInt32()
        self.firstFaceIndex = reader.readUInt32()
        self.faceCount = reader.readUInt32()
        boneCount = reader.readUInt32() # skip bone count
        reader.skip(boneCount * 4)
        return self


class SparkModel:
    def readData(self, reader):
        
        self.vertices = []
        self.indices = []
        self.faceSets = []
        self.materials = []
        self.boundsOrigin = Vector((0,0,0))
        self.boundsExtents = Vector((0,0,0))
        
        if reader.readData(4) != b'MDL\x07':
            raise SparkError("Unknown model format!")
        
        chunks = {}
        while not reader.doneReading():
            chunkIdx, chunkLength, chunkData = reader.readChunk()
            if chunkIdx in chunks:
                raise SparkError("Duplicate chunk index found!")
            chunks[chunkIdx] = chunkData
        
        # Read vertices
        vertexChunkReader = SparkReader(chunks[1])
        vertexCount = vertexChunkReader.readUInt32()
        self.vertices = [None] * vertexCount
        for i in range(vertexCount):
            self.vertices[i] = SparkVertex().readData(vertexChunkReader)
        
        # Read indices
        indicesChunkReader = SparkReader(chunks[2])
        indicesCount = indicesChunkReader.readUInt32()
        self.indices = [None] * indicesCount
        for i in range(indicesCount):
            self.indices[i] = indicesChunkReader.readUInt32()
        
        # Read face sets
        faceSetChunkReader = SparkReader(chunks[3])
        faceSetCount = faceSetChunkReader.readUInt32()
        self.faceSets = [None] * faceSetCount
        for i in range(faceSetCount):
            self.faceSets[i] = SparkFaceSet().readData(faceSetChunkReader)
        
        # Read materials
        materialsChunkReader = SparkReader(chunks[4])
        materialsCount = materialsChunkReader.readUInt32()
        self.materials = [None] * materialsCount
        for i in range(materialsCount):
            self.materials[i] = materialsChunkReader.readString()
        
        # Read bounding box
        boundingBoxChunkReader = SparkReader(chunks[17])
        self.boundsOrigin = boundingBoxChunkReader.readVec3()
        self.boundsExtents = boundingBoxChunkReader.readVec3()
        
        return self


class SparkEntity:
    def readData(self, reader):
        self.origin = Vector((0,0,0))
        self.angles = Euler(Vector((0,0,0)), 'XYZ')
        self.scale = Vector((1, 1, 1))
        self.modelFilePath = ""
        
        reader.readUInt32() # skip has layers...
        reader.readUInt32() # skip group idx
        
        self.className = reader.readString()
        if self.className != "prop_static":
            return
        
        propertyCount = reader.readUInt32()
        if propertyCount != 10:
            raise SparkError("Unexpected property count for prop_static entity!")
        
        for i in range(propertyCount):
            
            propertyChunkIdx, propertyChunkLength, propertyChunkData = reader.readChunk()
            if propertyChunkIdx != 2:
                continue
            
            propertyReader = SparkReader(propertyChunkData)
            propertyName = propertyReader.readString()
            
            if propertyName == "origin":
                if propertyReader.readUInt32() != 9: # origin must be distance-type
                    raise SparkError("Unexpected value type when reading property 'origin'.")
                if propertyReader.readUInt32() != 3: # must be 3 components.
                    raise SparkError("Unexpected component count when reading property 'origin'.")
                propertyReader.readUInt32() # skip animation value
                x = propertyReader.readFloat()
                y = propertyReader.readFloat()
                z = propertyReader.readFloat()
                self.origin = Vector((x, y, z))
                
            elif propertyName == "angles":
                if propertyReader.readUInt32() != 7: # angles must be angles-type
                    raise SparkError("Unexpected value type when reading property 'angles'.")
                if propertyReader.readUInt32() != 3: # must be 3 components.
                    raise SparkError("Unexpected component count when reading property 'angles'.")
                propertyReader.readUInt32() # skip animation value
                x = propertyReader.readFloat()
                y = propertyReader.readFloat()
                z = propertyReader.readFloat()
                self.angles = Euler(Vector((x, y, z)), 'XYZ')
                
            elif propertyName == "scale":
                if propertyReader.readUInt32() != 2: # scale must be real-type
                    raise SparkError("Unexpected value type when reading property 'scale'.")
                if propertyReader.readUInt32() != 3: # must be 3 components.
                    raise SparkError("Unexpected component count when reading property 'scale'.")
                propertyReader.readUInt32() # skip animation value
                x = propertyReader.readFloat()
                y = propertyReader.readFloat()
                z = propertyReader.readFloat()
                self.scale = Vector((x, y, z))
                
            elif propertyName == "model":
                if propertyReader.readUInt32() != 4: # model must be file-name-type
                    raise SparkError("Unexpected value type when reading property 'model'.")
                if propertyReader.readUInt32() != 1: # must be 1 component.
                    raise SparkError("Unexpected component count when reading property 'model'.")
                propertyReader.readUInt32() # skip animation value
                self.modelFilePath = propertyReader.readWString()
        return self


class SparkEntityData:
    def readData(self, data):
        self.staticProps = []
        
        reader = SparkReader(data)
        chunkType = 0
        
        # find the entity data.
        while not reader.doneReading() and chunkType != 1:
            chunkIdx, chunkLength, chunkData = reader.readChunk()
            chunkReader = SparkReader(chunkData)
            chunkType = chunkReader.readUInt16()
        
        if chunkType != 1:
            return # no entity data found.
        
        reader = chunkReader
        
        while not reader.doneReading():
            chunkIdx, chunkLength, chunkData = reader.readChunk()
            newEntity = SparkEntity().readData(SparkReader(chunkData))
            if newEntity.className == "prop_static":
                self.staticProps.append(newEntity)
        return self


class SparkLevelData:
    def readData(self, data):
        self.geoData = SparkGeoData().readData(data)
        self.entityData = SparkEntityData().readData(data)
        return self
    
    def writeData(self, writer):
        self.geoData.writeData(writer)


def appendList(l1, l2):
    for item in l2:
        l1.append(item)
    return l1


def materialInList(material, lst):
    if (lst.count(material) > 0):
        return lst.index(material)
    else:
        return -1


def mergeSparkData(mc1, mc2): ### Merge two sets of mesh chunks, the first input is the output.
    """Merges two spark data objects, effectively turning them into one mesh"""
    #First, let's intelligently merge the materials lists.  If there's any overlap, we'll need to adjust mc2's
    #material chunk to reference mc1's copy of the material.
    matRefs = []
    for i, mat in enumerate(mc2.materialChunk.materials):
        x = materialInList(mat, mc1.materialChunk.materials)
        if (x == -1): #material doesn't exist in mc1
            matRefs.append(len(mc1.materialChunk.materials)) #length of a list is equal to the index of the next item appended to it
            mc1.materialChunk.materials.append(mat) #add that material to the end of mc1's material list
        else: #material DOES exist in mc1
            matRefs.append(x) #index of where the identical material was found in mc1
     #We now have a list, "matRefs" that is effectively a map for mc2's material indices.        
   
           
     #Now, we append the second list of vertices to the first list of vertices.  Nothing special to do here,
     #but we need to keep in mind the starting number of vertices, so we can be sure to add this number to the
    #vertex id when referenced by mc2's edges.
    offset = len(mc1.vertexChunk.vertices)
    mc1.vertexChunk.vertices = appendList(mc1.vertexChunk.vertices, mc2.vertexChunk.vertices)
   
    for edge in mc2.edgeChunk.edges:
        edge.a +=offset
        edge.b +=offset
   
    #Now we merge the edge lists after offsetting the vertex indices within each edge of chunk #2.  We'll store
    #the offset for the faces chunk in the same manner as before.
    offset = len(mc1.edgeChunk.edges)
    mc1.edgeChunk.edges = appendList(mc1.edgeChunk.edges, mc2.edgeChunk.edges)
    
    for face in mc2.faceChunk.faces:
        face.material = matRefs[face.material]   #Quickly take care of some unfinished material business whilst
                                                 #in the neighborhood... so to speak... ;)
        for blmem in face.borderLoop.edgeLoopMembers:
            blmem.edge += offset
    mc1.faceChunk.faces = appendList(mc1.faceChunk.faces,mc2.faceChunk.faces)
    #I really don't care about mapping groups at the moment... maybe I'll add support in the future, but for now,
    #mc2's will just be lost.
    
    return mc1
