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





# ==========================================
# ======== OLD CODE !!!=====================
# ==========================================
'''
class SparkMeshChunkClipboard:
    """Contains all the sub-chunks that make up the mesh chunk"""
    def __init__(self, data):
        self.materialChunk = None
        self.vertexChunk = None
        self.edgeChunk = None
        self.faceChunk = None
        self.mappingChunk = None
        
        sD = SparkData(data)

        if (sD.readL() != 1):
            raise SparkError("Data in clipboard doesn't appear to be valid (header dword not 1)")
        
        rem = sD.readL() + 4

        if (sD.readS() != 2):
            raise SparkError("No geometry data detected in clipboard!")
        chunkOrder = [4,1,2,3,6,7,8]
        chunkNames = ["vertex", "edge", "face", "material", "unknown", "face-layers", "mapping", "geometry group"]
        expectedChunk = 0
        while (sD.dPt < (rem)):
            chunkID = sD.readL()
            if (chunkID != chunkOrder[expectedChunk]) and (expectedChunk < len(chunkOrder)):
                if (chunkID >= 1 and chunkID <= 8):
                    print("Warning2: Expected chunk ", chunkOrder[expectedChunk], " (", chunkNames[chunkOrder[expectedChunk]-1], "), but got chunk ", chunkID, " (", chunkNames[chunkID-1],") instead.  Proceeding with caution...")
                else:
                    print("Warning: Expected chunk ", chunkOrder[expectedChunk], " (", chunkNames[chunkOrder[expectedChunk]-1], "), but got chunk ", chunkID, " (unknown) instead.  Proceeding with caution...")
            if (chunkID == 4):
                self.materialChunk = SparkMaterialChunk()
                self.materialChunk.readData(sD)
            elif (chunkID == 1):
                self.vertexChunk = SparkVertexChunk()
                self.vertexChunk.readData(sD)
            elif (chunkID == 2):
                self.edgeChunk = SparkEdgeChunk()
                self.edgeChunk.readData(sD)
            elif (chunkID == 3):
                self.faceChunk = SparkFaceChunk()
                self.faceChunk.readData(sD)
            elif (chunkID == 6):
                sD.skipChunk()
            elif (chunkID == 7):
                self.mappingChunk = SparkMappingGroupChunk()
                self.mappingChunk.readData(sD)
            elif (chunkID == 8):
                sD.skipChunk()
            else:
                print("Warning: Unknown chunk detected.  Skipping, and attempting to proceed as usual.")
                sD.skipChunk()
                
            expectedChunk +=1
      
    def convertToBinString(self):
        ### Material Chunk ###
        materialChunkData = b''
        if (self.materialChunk == None):
            materialChunkData += writeL(1)
            materialChunkData += writeNString("materials/dev/dev_1024x1024.material")
        else:
            if (self.materialChunk.materials == None or self.materialChunk.materials == []):
                materialChunkData+= writeL(1)
                materialChunkData += writeNString("materials/dev/dev_1024x1024.material")
            else:
                materialChunkData+=writeL(len(self.materialChunk.materials))
                for material in self.materialChunk.materials:
                    materialChunkData+=writeNString(material)
        
        materialChunkData = writeL(4) + writeL(len(materialChunkData)) + materialChunkData
        
        ### Vertex Chunk ###
        vertexChunkData = b''
        if (self.vertexChunk == None):
            vertexChunkData += writeL(0)
        else:
            if (self.vertexChunk.vertices == None or self.vertexChunk.vertices == []):
                vertexChunkData += writeL(0)
            else:
                vertexChunkData += writeL(len(self.vertexChunk.vertices))
                for vertex in self.vertexChunk.vertices:
                    vertexChunkData+=writeF(vertex.x)
                    vertexChunkData+=writeF(vertex.y)
                    vertexChunkData+=writeF(vertex.z)
                    vertexChunkData+=writeB(1)
        vertexChunkData = writeL(1) + writeL(len(vertexChunkData)) + vertexChunkData
        
        ### Edge Chunk ###
        edgeChunkData = b''
        if (self.edgeChunk == None):
            edgeChunkData += writeL(0)
        else:
            if (self.edgeChunk.edges == None or self.edgeChunk.edges == []):
                edgeChunkData += writeL(0)
            else:
                edgeChunkData += writeL(len(self.edgeChunk.edges))
                for edge in self.edgeChunk.edges:
                    edgeChunkData+=writeL(edge.a)
                    edgeChunkData+=writeL(edge.b)
                    edgeChunkData+=writeB(1 if edge.smooth else 0)
        edgeChunkData = writeL(2) + writeL(len(edgeChunkData)) + edgeChunkData
        
        ### Face Chunk ###
        faceChunkData = b''
        if (self.faceChunk == None):
            faceChunkData += writeL(0)
        else:
            if (self.faceChunk.faces == None or self.faceChunk.faces == []):
                faceChunkData += writeL(0)
            else:
                faceChunkData+= writeL(len(self.faceChunk.faces))
                for face in self.faceChunk.faces:
                    faceChunkData+=writeF(face.angle)
                    faceChunkData+=writeF(face.xOffset)
                    faceChunkData+=writeF(face.yOffset)
                    faceChunkData+=writeF(face.xScale)
                    faceChunkData+=writeF(face.yScale)
                    faceChunkData+=writeL(face.mapping)
                    faceChunkData+=writeL(face.material)
                    faceChunkData+=writeL(0) #Blender doesn't support inner-loops
                    faceChunkData+=writeL(len(face.borderLoop.edgeLoopMembers))
                    for loop in face.borderLoop.edgeLoopMembers:
                        faceChunkData+=writeL(1 if loop.flipped else 0)
                        faceChunkData+=writeL(loop.edge)
        faceChunkData = writeL(3) + writeL(len(faceChunkData)) + faceChunkData
          
        ### Face-layers Chunk ###
        faceLayersChunkData = b''
        if (self.faceChunk == None):
            faceLayersChunkData += writeL(0)
        else:
            if (self.faceChunk.faces == None or self.faceChunk.faces == []):
                faceLayersChunkData += writeL(0)
            else:
                faceLayersChunkData+= writeL(len(self.faceChunk.faces))
                faceLayersChunkData+= writeL(2) #Format number (?)
                for face in self.faceChunk.faces:
                    faceLayersChunkData+= writeL(0) #Always 0...
        faceLayersChunkData = writeL(6) + writeL(len(faceLayersChunkData)) + faceLayersChunkData
          
        ### Mapping Chunk ###
        mappingChunkData = b''
        if (self.mappingChunk == None):
            mappingChunkData += writeL(0)
        else:
            if (self.mappingChunk.mappingGroups == None or self.mappingChunk.mappingGroups == []):
                mappingChunkData += writeL(0)
            else:
                mappingChunkData+= writeL(len(self.mappingChunk.mappingGroups))
                for map in self.mappingChunk.mappingGroups:
                    mappingChunkData+=writeL(map.id)
                    mappingChunkData+=writeF(map.angle)                     
                    mappingChunkData+=writeF(map.xScale)
                    mappingChunkData+=writeF(map.yScale)
                    mappingChunkData+=writeF(map.xOffset)
                    mappingChunkData+=writeF(map.yOffset)
                    mappingChunkData+=writeF(map.xNormal)
                    mappingChunkData+=writeF(map.yNormal)
                    mappingChunkData+=writeF(map.zNormal)
        mappingChunkData = writeL(7)+writeL(len(mappingChunkData))+mappingChunkData
        
        ### Geometry Group Chunk ###
        geometryGroupChunk = b''
        geometryGroupChunk += writeL(8) #Chunk Id = 8
        geometryGroupChunk += writeL(12) #Chunk length = 12 bytes
        geometryGroupChunk += writeL(0) #0 vertex groups
        geometryGroupChunk += writeL(0) #0 edge groups
        geometryGroupChunk += writeL(0) #0 face groups
        
        meshChunk = materialChunkData + vertexChunkData + edgeChunkData + faceChunkData + faceLayersChunkData + mappingChunkData + geometryGroupChunk
        meshChunk = writeS(2) + meshChunk
        meshChunk = writeL(1) + writeL(len(meshChunk)) + meshChunk
        
        return meshChunk

class SparkMaterialChunk:
    """Contains all the materials that are used in the level geometry"""
    def readData(self, sD):
        length = sD.readL()
        n = sD.readL()
        self.materials = []
        for i in range(0, n):
            self.materials.append(sD.readNString())

class SparkVertexChunk:
    """Contains all the vertices used in the level geometry"""
    def readData(self, sD):
        length = sD.readL()
        n = sD.readL()
        self.vertices = []
        for i in range(0, n):
            sV = SparkVertex()
            sV.readData(sD)
            self.vertices.append(sV)

class SparkVertex:
    """Contains a single set of vertex data"""
    def readData(self, sD):
        self.x = sD.readF()
        self.y = sD.readF()
        self.z = sD.readF()
        sD.nSkip(1) ## Skip that one extra byte that doesn't seem to do anything

class SparkEdgeChunk:
    """Contains all the edges used in the level geometry"""
    def readData(self, sD):
        length = sD.readL()
        n = sD.readL()
        self.edges = []
        for i in range(0, n):
            sE = SparkEdge()
            sE.readData(sD)
            self.edges.append(sE)

class SparkEdge:
    """Contains a single set of edge data"""
    def readData(self, sD):
        self.a = sD.readL()
        self.b = sD.readL()
        self.smooth = True if (sD.readB() == 1) else False

class SparkFaceChunk:
    """Contains all the faces used in the level geometry"""
    def readData(self, sD):
        length = sD.readL()
        n = sD.readL()
        self.faces = []
        for i in range(0, n):
            sF = SparkFace()
            sF.readData(sD)
            self.faces.append(sF)

class SparkFace:
    """Contains a single set of face data"""
    def readData(self, sD):
        self.angle = sD.readF()
        self.xOffset = sD.readF()
        self.yOffset = sD.readF()
        self.xScale = sD.readF()
        self.yScale = sD.readF()
        self.mapping = sD.readL() #(FF FF FF FF in hex)
        self.material = sD.readL()
        numInnerLoops = sD.readL()
        self.borderLoop = SparkEdgeLoop()
        self.borderLoop.readData(sD)
        self.innerLoops = []
        for i in range(0,numInnerLoops):
            sEL = SparkEdgeLoop()
            sEL.readData(sD)
            self.innerLoops.append(sEL)

class SparkEdgeLoop:
    """Contains a single edge loop"""
    def readData(self, sD):
        numEdges = sD.readL()
        self.edgeLoopMembers = []
        for i in range(0,numEdges):
            selm = SparkEdgeLoopMember()
            selm.readData(sD)
            self.edgeLoopMembers.append(selm)

class SparkEdgeLoopMember:
    """Contains a single edge loop member"""
    def readData(self, sD):
        self.flipped = True if (sD.readL() == 1) else False
        self.edge = sD.readL()

class SparkMappingGroupChunk:
    """Contains the mapping group information"""
    def readData(self, sD):
        length = sD.readL()
        n = sD.readL()
        self.mappingGroups = []
        for i in range(0, n):
            sMG = SparkMappingGroup()
            sMG.readData(sD)
            self.mappingGroups.append(sMG)
    
    def getMappingByID(self, id):
        for i,map in enumerate(self.mappingGroups):
            if map.id == id:
                return i
        return -1

class SparkMappingGroup:
    """Contains a single mapping group"""
    def readData(self, sD):
        self.id = sD.readL()
        self.angle = sD.readF()
        self.xScale = sD.readF()
        self.yScale = sD.readF()
        self.xOffset = sD.readF()
        self.yOffset = sD.readF()
        self.xNormal = sD.readF()
        self.yNormal = sD.readF()
        self.zNormal = sD.readF()
        
class SparkError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SparkData: ###Spark binary data
    def __init__(self, data):
        self.data = data
        self.dPt = 0
        
    def doneReading(self):
        return len(self.data) <= self.dPt
        
    def readL(self): ### Read 4 byte integer
        """Reads the next 4-byte integer from the data, and returns it"""
        if (len(self.data) < self.dPt +4):
            raise SparkError("Unexpected end of data stream when reading a 4-byte integer!")
        else:
            r = struct.unpack("<L", self.data[self.dPt:self.dPt+4])
            self.dPt += 4
            return r[0]
    
    def readF(self): ### Read 4 byte float
        """Reads the next 4-byte float from the data, and returns it"""
        if (len(self.data) < self.dPt +4):
            raise SparkError("Unexpected end of data stream when reading a 4-byte float!")
        else:
            r = struct.unpack("<f", self.data[self.dPt:self.dPt+4])
            self.dPt += 4
            return r[0]
        
    def readS(self): ### Read 2 byte integer
        """Reads the next 2-byte integer from the data, and returns it"""
        if (len(self.data) < self.dPt +2):
            raise SparkError("Unexpected end of data stream when reading a 2-byte integer!")
        else:
            r = struct.unpack("<H", self.data[self.dPt:self.dPt+2])
            self.dPt += 2
            return r[0]
    
    def readB(self): ### Read 1 byte, return an integer
        """Reads the next byte from the data, and returns it"""
        if (len(self.data) < self.dPt+1):
            raise SparkError("Unexpected end of data stream when reading a single byte!")
        else:
            r = self.data[self.dPt]
            self.dPt += 1
            return r
        
    def readNString(self): ### Read narrow string
        """Reads a narrow string from the data.  Narrow strings are 1-byte per character strings, that are prefixed with the string length as a 4-byte integer."""
        length = self.readL()
        if (len(self.data) < self.dPt +length):
            raise SparkError("Unexpected end of data stream when reading a narrow string!")
        else:
            bOut = self.data[self.dPt:self.dPt+length]
            self.dPt = self.dPt+length
            return bOut.decode()
    
    def nSkip(self, n): ### skip n bytes
        """Skips the next N number of bytes in the string of data"""
        if (self.dPt + n < 0):
            raise SparkError("Attempt to index data out of bounds (<0)")
        elif (self.dPt + n > len(self.data)):
            raise SparkError("Attempt to index data out of bounds (>data length)")
        else:
            self.dPt += n
            
    def skipChunk(self): ### skips an entire chunk using the length field
        """Skips the entire chunk by using the first 4 bytes which are presumably the length field of the chunk to skip.  If not... you're doing it wrong."""
        length = self.readL()
        self.nSkip(length)
        
def writeL(value): ### Write a 4 byte integer ###
    """Returns a byte-string representation of the integer passed to it"""
    str = b''
    str+= struct.pack("<L",value)
    return str

def writeF(value): ### Write a 4 byte float ###
    """Returns a byte-string representation of the float passed to it"""
    str = b''
    str+= struct.pack("<f", value)
    return str

def writeS(value): ### Write a 2 byte integer ###
    """Returns a byte-string representation of the unsigned short passed to it"""
    str = b''
    str+= struct.pack("<H", value)
    return str

def writeB(value): ### Write a single byte
    """Returns a byte-string representation of a single byte"""
    str = b''
    str+= struct.pack("<B", value)
    return str

def writeNString(value): ### Write narrow string
    """Returns a byte-string representation of a narrow string, including the 4-byte length field at the beginning"""
    val = str.encode(value)
    bstr = b''
    bstr += struct.pack("<L", len(val))
    for i in range(0,len(val)):
        bstr += struct.pack("<c", val[i:i+1])
    return bstr

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
            blmem.edge+= offset
    mc1.faceChunk.faces = appendList(mc1.faceChunk.faces,mc2.faceChunk.faces)
    #I really don't care about mapping groups at the moment... maybe I'll add support in the future, but for now,
    #mc2's will just be lost.
    for face in mc1.faceChunk.faces:
        print("material#:",face.material)
    return mc1

'''
