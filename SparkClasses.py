# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 22, 2014

import struct

class SparkPropChunksClipboard:
    """Contains all prop chunk data."""
    def __init__(self, data):
        
        sD = SparkData(data)
        
        if (sD.readL() != 1):
            raise SparkError("Data in clipboard doesn't appear to be valid (header dword not 1)")
        
        currentPosition = sD.dPt
        nextChunk = currentPosition + sD.readL()
        while not sD.doneReading():
            
        

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
