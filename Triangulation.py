# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 22, 2014
# Special thanks to Max McGuire for providing C++ source!
# Never would have figured this out without that help. :)

from . import SparkClasses
import math

class vert2D:
    """2d vertex"""
    def __init__(self,vX,vY,id):
        self.x = vX
        self.y = vY
        self.realId = id
    def __str__(self):
        return ('( ' + str(self.x*39.37) + ' , ' + str(self.y*39.37) + ') id='+str(self.realId))
        
class triangle:
    """Simple triangle that references two "vert2D" objects"""
    def __init__(self, vert1, vert2, vert3):
        self.v1 = vert1
        self.v2 = vert2
        self.v3 = vert3

def cross(a,b):
    """Taken from http://stackoverflow.com/questions/1984799/cross-product-of-2-different-vectors-in-python"""
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]
    return c
        
def get3Verts(verts, earV):
    v1 = verts[((earV-1)+len(verts))%len(verts)]
    v2 = verts[earV]
    v3 = verts[(earV+1)%len(verts)]
    vertTriple = [v1,v2,v3]
    return vertTriple
        
def PointInTriangle(p, v1, v2, v3):
    # Adapted from: http://stackoverflow.com/questions/2049582/how-to-determine-a-point-in-a-triangle
    area = 0.5*(-v2.y*v3.x + v1.y*(-v2.x + v3.x) + v1.x*(v2.y - v3.y) + v2.x*v3.y)
    if area <= 0.00001: #Either a tiny sliver or inline point
        return False
    
    s = 1.0 / (2.0 * area)*(v1.y*v3.x - v1.x*v3.y + (v3.y - v1.y)*p.x + (v1.x - v3.x)*p.y);
    t = 1.0 / (2.0 * area)*(v1.x*v2.y - v1.y*v2.x + (v1.y - v2.y)*p.x + (v2.x - v1.x)*p.y);
    
    if ( s > 0 ) and ( t > 0 ) and ( 1.0 - s - t > 0 ):
        return True
    else:
        return False
    
def IsConvex(v1, v2, v3):
    area = (v2.x - v1.x) * (v3.y - v1.y) - (v2.y - v1.y) * (v3.x - v1.x)
    '''###DEBUG PRINT
    print("CalculatedAreaValue:",area)'''
    return (area >= 0.0001)

def UnitVector(vect):
    mag = math.sqrt((vect[0] * vect[0] )+ (vect[1] * vect[1]))
    vect[0] = vect[0]/mag
    vect[1] = vect[1]/mag

def MaxMinAngle(v1,v2,v3):
    e1=[v1.x-v2.x, v1.y-v2.y]
    e2=[v1.x-v3.x, v1.y-v3.y]
    e3=[v2.x-v3.x, v2.y-v3.y]
    UnitVector(e1)
    UnitVector(e2)
    UnitVector(e3)
    
    minA = abs(e1[0]*e2[0] + e1[1]*e2[1])
    minA = min(minA,abs(e1[0]*e3[0] + e1[1]*e3[1]))
    minA = min(minA,abs(e3[0]*e2[0] + e3[1]*e2[1]))
    
    return minA


def IsEar(verts, v1, v2, v3):
    if (not IsConvex(v1,v2,v3)):
        '''###DEBUG PRINT
        print("    not convex...")'''
        return False
    
    for v in verts:
        if (v is v1 or v is v2 or v is v3):
            continue
        
        if (PointInTriangle(v, v1,v2,v3)):
            '''###DEBUG PRINT
            print("    point contained triangle")'''
            return False
    return True

def GetHoleMaxX(hole):
    maxX = hole[0].x
    for i in range(1,len(hole)):
        maxX = max(maxX, hole[i].x)
    return maxX

def GetHoleMaxXVert(hole):
    maxX = hole[0].x
    maxXVert = 0
    for i in range(1,len(hole)):
        if (hole[i].x > maxX):
            maxX = hole[i].x
            maxXVert = i
    return maxXVert
    
def SortHolesByMaxX(holes):
    newHoles = []
    
    while (len(holes) > 1):
        maxXIndex = 0
        maxXValue = GetHoleMaxX(holes[0])
        for i in range(1,len(holes)):
            testVal = GetHoleMaxX(holes[i])
            if testVal > maxXValue:
                maxXIndex = i
                maxXValue = testVal
        newHoles.append(holes.pop(maxXIndex))
    newHoles.append(holes.pop())
    
    return newHoles

def ProcessHoles(border, holes):
    # Based on the algorithm outlined here:
    # http://www.geometrictools.com/Documentation/TriangulationByEarClipping.pdf
    if (holes == None) or (holes == []): #If no holes, no work needs to be done!
        return
    '''###Debug Print
    print("Before Sorting:")
    for i in range(0,len(holes)):
        print("Hole ",i,":",sep='')
        for j in range(0,len(holes[i])):
            print("( %.3f" % (holes[i][j].x*39.37)," , %.3f )" %(holes[i][j].y*39.37))'''
    if (len(holes) > 1):
        holes = SortHolesByMaxX(holes)
        
    '''###Debug Print
    print("\nAfter Sorting:")
    for i in range(0,len(holes)):
        print("Hole ",i,":",sep='')
        for j in range(0,len(holes[i])):
            print("( %.3f" % (holes[i][j].x*39.37)," , %.3f )" %(holes[i][j].y*39.37))'''
    for hole in holes:
        maxXV = GetHoleMaxXVert(hole)
        
        tMin = None
        intersectVertexIndex1 = 0
        intersectVertexIndex2 = 0
        
        for i in range(0,len(border)):
            v1 = border[i]
            v2 = border[(i+1)%len(border)]
            
            if ( v1.y > hole[maxXV].y) or (v2.y < hole[maxXV].y): #Ensure edge even intersects ray
                continue
            
            vertIndex1 = i
            vertIndex2 = (i + 1) % len(border)
            t = None
            
            if ((v2.y - v1.y) != 0.00):
                t = (v1.x - hole[maxXV].x) + (hole[maxXV].y - v1.y) * (v2.x - v1.x) / (v2.y - v1.y)
                #Check if the ray hits a vertex
                if (v1.y == hole[maxXV].y):
                    vertIndex2 = vertIndex1
                elif (v2.y == hole[maxXV].y):
                    vertIndex1 = vertIndex2
            else:
                #Edge is parallel to the ray, so it hits the vertex with minimum X
                if (v1.x < v2.x):
                    t = v1.x - hole[maxXV].x
                    vertIndex2 = vertIndex1
                else:
                    t = v2.x - hole[maxXV].x
                    vertIndex1 = vertIndex2
            
            if (t >= 0.0 and (tMin == None or t < tMin)):
                tMin = t
                intersectVertexIndex1 = vertIndex1
                intersectVertexIndex2 = vertIndex2
                
        intersectPoint = vert2D(hole[maxXV].x + tMin, hole[maxXV].y, None)
        insertIndex = 0
        
        if (intersectVertexIndex1 == intersectVertexIndex2):
            #We hit a vertex
            insertIndex = intersectVertexIndex1
        else:
            pointIndex = 0
            if (border[intersectVertexIndex1].x > border[intersectVertexIndex2].x):
                pointIndex = intersectVertexIndex1
            else:
                pointIndex = intersectVertexIndex2
            
            ##Check for reflex, border vertices inside the triangle formed by maxX, intersect point, and p.
            insertIndex = pointIndex
            
            point = border[pointIndex]
            
            dX = border[insertIndex].x - hole[maxXV].x
            dY = border[insertIndex].y - hole[maxXV].y
            
            maxLengthSquared = ((dX * dX) + (dY * dY))
            maxCosSquared = math.sqrt(dX) / maxLengthSquared
            
            for i in range(0,len(border)):
                if ( i != pointIndex ):
                    v1 = border[((i+(len(border)-1))%len(border))]
                    v2 = border[i]
                    v3 = border[((i+1)%len(border))]
                    if ( (not IsConvex(v1,v2,v3) ) and PointInTriangle( border[i] , hole[maxXV] , intersectPoint , point )):
                        dX = border[i].x - hole[maxXV].x
                        dY = border[i].y - hole[maxXV].y
                        lengthSquared = ((dX * dX) + (dY * dY))
                        cosSquared = math.sqrt(dX) / lengthSquared
                        
                        if (cosSquared > maxCosSquared):
                            maxCosSquared = cosSquared
                            maxLengthSquared = lengthSquared
                            insertIndex = i
                        elif ((cosSquared == maxCosSquared) and (lengthSquared < maxLengthSquared)):
                            #Reflex vertex has angle equal to the current minimum but the length is smaller
                            #so it becomes the new visible candidate
                            maxLengthSquared = lengthSquared
                            insertIndex = i
        
        #Now we just have to create two virtual vertices and merge the hole verts with the border verts in the proper order
        for i in range(0,len(hole)):
            border.insert(insertIndex + 1 + i, hole[(i + maxXV) % len(hole)])
        border.insert(insertIndex + 1 + len(hole), hole[maxXV])
        border.insert(insertIndex + 2 + len(hole), border[insertIndex])
    

class polygon:
    """A polygon for triangulation, created from a Spark Face"""
    def __init__(self, sF, sD):
        vertices= sD.vertexChunk.vertices
        edges = sD.edgeChunk.edges
        self.triangles = []
        
        #Guess the normal vector of the polygon by picking 3 adjacent vertices from the
        #border edge until a vaild triplet is found

        length = len(sF.borderLoop.edgeLoopMembers) #Number of vertices in border loop
        if (length < 3):
            raise SparkError("ERROR:  Attempt to triangulate polygon with less than 3 vertices.  WHAT DID YOU DO???????")
        nVec = (0,1,0)
        for i in range(0,length):
            vertIndex1 = ((i-1)+length)%length
            vertIndex3 = (i+1)%length
            
            v1 = vertices[edges[sF.borderLoop.edgeLoopMembers[vertIndex1].edge].b] if sF.borderLoop.edgeLoopMembers[vertIndex1].flipped else vertices[edges[sF.borderLoop.edgeLoopMembers[vertIndex1].edge].a]
            v2 = vertices[edges[sF.borderLoop.edgeLoopMembers[i].edge].b] if sF.borderLoop.edgeLoopMembers[i].flipped else vertices[edges[sF.borderLoop.edgeLoopMembers[i].edge].a]
            v3 = vertices[edges[sF.borderLoop.edgeLoopMembers[vertIndex3].edge].b] if sF.borderLoop.edgeLoopMembers[vertIndex3].flipped else vertices[edges[sF.borderLoop.edgeLoopMembers[vertIndex3].edge].a]
            
            vec1 = ( v1.x-v2.x , v1.y-v2.y , v1.z-v2.z )
            vec2 = ( v3.x-v2.x , v3.y-v2.y , v3.z-v2.z )
            
            nVec = cross(vec1,vec2)
            for i in range(0,len(nVec)):
                nVec[i] = abs(nVec[i])
            if (nVec[0] > 0.00001) or (nVec[1] > 0.00001) or (nVec[2] > 0.00001): #Acceptable cross product value.  Was checking for in-line vertices, loop may terminate
                break;
        
        self.verts = [] #border loop vertices
        self.holes = [] #inner loop vertices
        
        '''###DEBUG PRINT
        print("Guess NORMAL VECTOR =",nVec)'''
        
        if (nVec[0] >= nVec[1]) and (nVec[0] >= nVec[2]):
            #X is least significant
            '''###DEBUG PRINT
            print("X is least significant")'''
            for mem in sF.borderLoop.edgeLoopMembers:
                if not mem.flipped:
                    self.verts.append( vert2D(vertices[edges[mem.edge].a].z , vertices[edges[mem.edge].a].y, edges[mem.edge].a ))
                else:
                    self.verts.append( vert2D(vertices[edges[mem.edge].b].z , vertices[edges[mem.edge].b].y, edges[mem.edge].b ))
            
            for il in sF.innerLoops:
                holeVerts = []
                for mem in il.edgeLoopMembers:
                    if not mem.flipped:
                        holeVerts.append( vert2D(vertices[edges[mem.edge].a].z , vertices[edges[mem.edge].a].y, edges[mem.edge].a ))
                    else:
                        holeVerts.append( vert2D(vertices[edges[mem.edge].b].z , vertices[edges[mem.edge].b].y, edges[mem.edge].b ))
                self.holes.append(holeVerts)
            
        elif (nVec[1] > nVec[0]) and (nVec[1] >= nVec[2]):
            #Y is least significant
            '''###DEBUG PRINT
            print("Y is least significant")'''
            for mem in sF.borderLoop.edgeLoopMembers:
                if not mem.flipped:
                    self.verts.append( vert2D( vertices[edges[mem.edge].a].x , vertices[edges[mem.edge].a].z, edges[mem.edge].a ))
                else:
                    self.verts.append( vert2D( vertices[edges[mem.edge].b].x , vertices[edges[mem.edge].b].z, edges[mem.edge].b ))
            
            for il in sF.innerLoops:
                holeVerts = []
                for mem in il.edgeLoopMembers:
                    if not mem.flipped:
                        holeVerts.append( vert2D( vertices[edges[mem.edge].a].x , vertices[edges[mem.edge].a].z, edges[mem.edge].a ))
                    else:
                        holeVerts.append( vert2D( vertices[edges[mem.edge].b].x , vertices[edges[mem.edge].b].z, edges[mem.edge].b ))
                self.holes.append(holeVerts)
            
        else:
            #Z is least significant
            '''###DEBUG PRINT
            print("Z is least significant")'''
            for mem in sF.borderLoop.edgeLoopMembers:
                if not mem.flipped:
                    self.verts.append( vert2D( vertices[edges[mem.edge].a].x , vertices[edges[mem.edge].a].y, edges[mem.edge].a ))
                else:
                    self.verts.append( vert2D( vertices[edges[mem.edge].b].x , vertices[edges[mem.edge].b].y, edges[mem.edge].b ))
            
            for il in sF.innerLoops:
                holeVerts = []
                for mem in il.edgeLoopMembers:
                    if not mem.flipped:
                        holeVerts.append( vert2D( vertices[edges[mem.edge].a].x , vertices[edges[mem.edge].a].y, edges[mem.edge].a ))
                    else:
                        holeVerts.append( vert2D( vertices[edges[mem.edge].b].x , vertices[edges[mem.edge].b].y, edges[mem.edge].b ))
                self.holes.append(holeVerts)
        #Now we need to ensure that the vert order is counter-clockwise
        area = 0.0
        vert_order_reversed = False
        for i in range(0,len(self.verts)):
            x1 = self.verts[i].x
            y1 = self.verts[i].y
            x2 = self.verts[(i+1) % len(self.verts)].x
            y2 = self.verts[(i+1) % len(self.verts)].y
            
            area+= (x1 * y2 - x2 * y1)
        
        if (area < 0.0):
            '''###DEBUG Print
            print("reversing vert order!!!")'''
            vert_order_reversed = True
            self.verts.reverse()
            
        #Now, we need to do the same for the vert order of the holes, but they need to be clockwise
        for hole in self.holes:
            area = 0.0
            for i in range(0,len(hole)):
                x1 = hole[i].x
                y1 = hole[i].y
                x2 = hole[(i+1) % len(hole)].x
                y2 = hole[(i+1) % len(hole)].y
                
                area+= (x1 * y2 - x2 * y1)
            
            if (area > 0.0):
                hole.reverse()
        
        #Now, before we can start triangulating, we need to get rid of any holes.
        holes = self.holes
        border = self.verts
        
        #Quick sanity-check to make sure there's no <3 length holes in the list
        for i in range(0,len(holes)):
            if len(holes[i]) < 3:
                holes[i] = None
        holes[:] = [h for h in holes if h!=None]
        
        ProcessHoles(border, holes)
        
        """###DEBUG VERBOSITY###
        print("TRIANGULATION VERTS AFTER HOLE FIXING:")
        for i,v in enumerate(border):
            print("    ",i,":", v.realId)"""
        
        # Now we can start triangulating by clipping off ears.  To get nice results, we're going to first gather a list of all
        # the candidate "ears".  An ear is a triangle formed by 3 consecutive vertices that is convex, and contains no other
        # vertices from the same polygon.  We will sort this list of ears by the maximum minumum interior angle.
        while (len(border) > 3):
            ears = [] #stores the border[] list index of the vertex, not a reference to the vertex
            for i in range(0, len(border)):
                v1 = border[(i + (len(border)-1)) % (len(border))]
                v2 = border[i]
                v3 = border[(i+1)%(len(border))]
                '''###DEBUG
                print("Checking vert:",i)
                print("V1:",v1)
                print("V2:",v2)
                print("V3:",v3)'''
                if (IsEar(border, v1, v2, v3)):
                    ears.append(i)
            
            '''###DEBUG PRINTING###
            print("EAR LIST")
            for i,e in enumerate(ears):
                print("    ",i,'-',e)'''
            
            
            sEars = [] ##sorted ears
            while(len(ears) >0):
                if (len(ears) == 1):
                    sEars.append(ears[0])
                    ears.pop(0)
                else:
                    maxE = 0
                    triple = get3Verts(border, ears[0])
                    minVal = MaxMinAngle(triple[0],triple[1],triple[2])
                    for i in range(1,len(ears)):
                        triple = get3Verts(border, ears[i])
                        minCandidate = MaxMinAngle(triple[0],triple[1],triple[2])
                        if (minCandidate > minVal):
                            maxE = i
                            minval = minCandidate
                    sEars.append(ears[maxE])
                    ears.pop(maxE)
            
            #Now we have the best candidate for the ear at the top of the sorted list, let's use it.
            if len(sEars) == 0:
                break
            earVerts = get3Verts(border,sEars[0])
            self.triangles.append(triangle(earVerts[0],earVerts[1],earVerts[2]))
            border.pop(sEars[0])
        
        self.triangles.append(triangle(border[0], border[1], border[2]))
        if vert_order_reversed:
            for t in self.triangles:
                temp_vert = t.v1
                t.v1 = t.v3
                t.v3 = temp_vert
