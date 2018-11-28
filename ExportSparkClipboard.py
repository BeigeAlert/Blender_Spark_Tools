# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 28, 2018

# Ugh... this is an awful hot mess that needs rewriting... :(

import bpy
from . import SparkClasses
from . import ClipUtils
import bmesh
import math
import os

def INCHESPERMETER(): return 39.3700787

def FindMaterial(m, materials):
    try:
        materials.index(m)
    except ValueError:
        return False
    return True


def CleanMaterialPath(m):
    """Strips off everything up to and including the "ns2" or "output" part of the material path, leaving everything to the right of it.  Then changes the file extension to .material"""
    m = m.replace('\\','/') #Replace backslashes with forward slashes.  That's the way spark takes em, and luckily blender doesn't have a problem with it.
    f = m.split("/")
    
    for i in range(0,len(f)):
        s = f.pop(0)
        if (s == "output") or (s == "ns2"):
            break
    
    n = f.pop(-1).split(".")
    n.pop(-1)
    n.append("material")
    f.append('.'.join(n))
    
    m = '/'.join(f)
    return m


def AddMaterial(mat, materials):
    """Adds the material to the list of materials and returns the new index if the material is not already in the list.  Otherwise, the index of the existing entry is returned"""
    m = CleanMaterialPath(mat)
    
    if (not FindMaterial(m, materials)):
        materials.append(m)
    return materials.index(m)
    
    
class sparkTex:
    def __init__(self):
        self.angle = 0.0
        self.xOffs = 0.0
        self.yOffs = 0.0
        self.xScale = 1.0
        self.yScale = 1.0
        self.image = None
        
        
class coord:
    def __init__(self, xC, yC, zC):
        self.x = xC
        self.y = yC
        self.z = zC
        
        
def CalculateSparkTex(poly, me, CORRECT_UNIT_FACTOR, auto_tex = None):
    norm = [poly.normal[0], poly.normal[1], poly.normal[2]]
    vertList = []
    sTex = sparkTex()
    
    if (me.uv_textures.active == None): #No UV layers = no textures on this mesh.  Slapping the default on there.
        print("WARNING: No UV layers detected on mesh '", me.name, "'.  Using default texture...")
        return sTex
    
    faceTex = me.uv_textures.active.data[poly.index].image
    if (faceTex == None or faceTex.size[0] == 0 or faceTex.size[1] == 0): #No UV texture present for this face.  Slapping the default on there.
        print("WARNING: Face ID ", poly.index, " is missing a UV texture.  Using default texture...")
        return sTex
    
    #Create a new list of verts so we don't screw up the data with our calculations
    for i in poly.loop_indices:
        v = me.vertices[me.loops[i].vertex_index]
        vertList.append( coord( v.co[0], v.co[1], v.co[2]))
        
    #Now, let's figure out if the polygon is already flat or not.
    #3 scenarios: 1) it's flat, 2) it's flat but facing down, or 3) some arbitrary angle
    if ( ( abs(  norm[0]) < 0.00001) and (abs(norm[1])<0.00001) and (norm[2] >= 0.99998)):
        #Normal is close enough to straight up
        norm[0] = 0.0
        norm[1] = 0.0
        norm[2] = 1.0
        #Rotating all the coordinates 90 degrees.  Yea this is a really roundabout way of fixing
        #my screwed up math (see 'else'), but hey, if it works, it ain't stupid... right?  RIGHT?????
        for v in vertList:
            x = v.x
            v.x = v.y
            v.y = -x
    elif ( ( abs( norm[0]) < 0.00001) and (abs(norm[1])< 0.00001) and (norm[2] <= -0.99998)):
        #Normal is close enough to straight down
        norm[0] = 0.0
        norm[1] = 0.0
        norm[2] = 1.0
        for v in vertList:
            x = v.x
            v.x = -v.y
            v.y = x
            v.z = -v.z
    else:
        #The face is an arbitrary angle, so we've got work to do
        a = math.pi - math.atan2( norm[1], norm[0]) #calculate the normal's yaw (blender z)
        #print("yaw = ", a*(180.0/math.pi))
        for v in vertList:
            x = v.x*math.cos(a) - v.y*math.sin(a)
            y = v.x*math.sin(a) + v.y*math.cos(a)
            v.x = x
            v.y = y
            #print("    vert: (",v.x*39.37, " , ", v.y*39.37," , ", v.z*39.37, " )")
        #We've rotated the coordinates such that the yaw is 0, the new x component of the normal
        #is the combined former length of the x and y components.  The y component is now 0.
        norm[0] = math.sqrt((norm[0]*norm[0]) + (norm[1] * norm[1]))
        norm[1] = 0.0
        
        #Now we do the same thing with the pitch
        a = -(math.atan2(norm[0],norm[2]))
        #print("pitch = ", a*(180.0/math.pi))
        for v in vertList:
            v.x = v.x * math.cos(a) - v.z*math.sin(a)
            z = v.x*math.sin(a) + v.z * math.cos(a)
            #print("    vert: (",v.x*39.37, " , ", v.y*39.37," , ", z*39.37, " )")
            
    #Now, we have some nice, flat 2d-ish coordinates for the polygon. (I say "ish" because
    #it's still technically 3d... it's just perfectly flat as well).
    #Time to compare these 3d coordinates to the corresponding UV coordinates.  The way we're
    #going to do that is by taking the difference in angle between each edge, and the
    #corresponding UV-edge.  For each difference-angle we have, we convert that to a unit vector,
    #multiply that by the edge length -- to give longer edges more weight -- then take the sum of
    #the vectors, and divide that by the total weight, then convert that vector back to an angle.
    #This gives us a very good approximation of the ideal texture angle, based on the UV coordinates.
    vectorSum = [0.0,0.0]
    size = len(vertList)
    img = me.uv_textures.active.data[poly.index].image
    imgX = img.size[0]
    imgY = img.size[1]
    aspect = imgX/imgY #aspect ratio of the image.  Very important to take into account.

    for i, vL in enumerate(vertList):
        xV = vertList[i].x - vertList[(i+1)%size].x
        yV = vertList[i].y - vertList[(i+1)%size].y
        xU1 = me.uv_layers[0].data[poly.loop_start+i].uv[0]
        yU1 = me.uv_layers[0].data[poly.loop_start+i].uv[1]
        xU2 = me.uv_layers[0].data[poly.loop_start+(i+1)%size].uv[0]
        yU2 = me.uv_layers[0].data[poly.loop_start+(i+1)%size].uv[1]
        
        weight = math.sqrt( xV*xV + yV*yV) #length of 3d edge
        angleP = math.atan2( yV, xV) #P is for polygon
        angleU = math.atan2( (yU1-yU2)/aspect , xU1-xU2) # U is for UV
        
        dAngle = angleP - angleU
        vectorSum[0] = vectorSum[0] + weight*math.cos(dAngle)
        vectorSum[1] = vectorSum[1] + weight*math.sin(dAngle)
    
    angle = math.atan2(vectorSum[1], vectorSum[0]) #+ texAngleVal
    #print("texAngle = ", angle*(180.0/math.pi))
    #To accomodate the size and shift calculations, we're going to rotate all the vertices one last
    #time, to cancel out the texture angle, taking into account the aspect ratio of the image.
    BBoxPoly = [ 9999999.99 , 9999999.99 , -9999999.99 , -9999999.99 ] #-X side, -Y side, +X side, +Y side
    BBoxUV = [ 9999999.99 , 9999999.99 , -9999999.99 , -9999999.99 ] #-X side, -Y side, +X side, +Y side
    for v in vertList:
        x = v.x*math.cos(-angle) - v.y*math.sin(-angle)
        y = v.x*math.sin(-angle) + v.y*math.cos(-angle)
        v.x = x
        v.y = y
        
        if x < BBoxPoly[0]:
            BBoxPoly[0] = x
        if x > BBoxPoly[2]:
            BBoxPoly[2] = x
        if y < BBoxPoly[1]:
            BBoxPoly[1] = y
        if y > BBoxPoly[3]:
            BBoxPoly[3] = y
    
    #print("VERTS: ")
    #for v in vertList:
    #    print("    ( ", v.x, " , ", v.y, " ) ")
    for i, v in enumerate(vertList):
        x = me.uv_layers[0].data[poly.loop_start+i].uv[0]
        y = me.uv_layers[0].data[poly.loop_start+i].uv[1]
        
        #print("Y:",y)
        
        if x < BBoxUV[0]:
            BBoxUV[0] = x
        if x > BBoxUV[2]:
            BBoxUV[2] = x
        if y < BBoxUV[1]:
            BBoxUV[1] = y
        if y > BBoxUV[3]:
            BBoxUV[3] = y
    #Now we just need to figure out the scales and shifts.
    uvSpreadX = BBoxUV[2] - BBoxUV[0]
    
    #print("BBoxUV[3]:",BBoxUV[3],"    BBoxUV[1]:",BBoxUV[1])
    uvSpreadY = BBoxUV[3] - BBoxUV[1]
    polySizeX = BBoxPoly[2] - BBoxPoly[0]
    polySizeY = BBoxPoly[3] - BBoxPoly[1]
    
    #print("uvspreadY:",uvSpreadY,"    polySizeY:",polySizeY)
    
    ScaleX = uvSpreadX / polySizeX
    ScaleY = uvSpreadY / polySizeY
    
    #print("ScaleY:",ScaleY, "   imgY:",imgY)
    
    #Dummy checks.  If ScaleX/Y or imgX/Y is zero, we'll disable texture export here.
    if ScaleX == 0.0 or ScaleY == 0.0 or imgX == 0 or imgY == 0:
        return None
    
    scaleFactorX = ( 8 * CORRECT_UNIT_FACTOR ) / ( ScaleX * imgX)
    scaleFactorY = ( 8 * CORRECT_UNIT_FACTOR ) / ( ScaleY * imgY)
    
    CenterX = (BBoxPoly[2] + BBoxPoly[0]) / 2.0
    CenterY = (BBoxPoly[3] + BBoxPoly[1]) / 2.0
    CenterU = (BBoxUV[2] + BBoxUV[0]) / 2.0
    CenterV = (BBoxUV[3] + BBoxUV[1]) / 2.0
    
    ShiftX = CenterU - (CenterX * ScaleX)
    ShiftY = (CenterY * ScaleY) - CenterV
    
    textureSettings = sparkTex()
    textureSettings.angle = -angle - (math.pi/2)
    textureSettings.xOffs = ShiftX
    textureSettings.yOffs = ShiftY
    textureSettings.xScale = ScaleX
    textureSettings.yScale = ScaleY
    textureSettings.image = img
    
    return textureSettings
    

def ExportClipboardData(operator, context,
        selection_only = True,
        correct_units = True,
        correct_axes = True,
        export_textures = True,
        ):
    from mathutils import Matrix
    scene = bpy.context.scene
    obs = bpy.context.selected_objects if selection_only else bpy.context.visible_objects
    
    scaleMat = Matrix.Scale(1.0/INCHESPERMETER(),4)
    
    materials = []
    
    mDatTotal = None
    
    CORRECT_UNIT_FACTOR = 1.0
    if (correct_units):
        CORRECT_UNIT_FACTOR = INCHESPERMETER()
    
    for object in obs:
        if not object.type == 'MESH':
            continue
        me = object.to_mesh(scene = scene, apply_modifiers = True, settings = 'PREVIEW')
        me.transform(object.matrix_world)
        if (correct_units):
            me.transform(scaleMat)
        
        levelData = SparkClasses.SparkLevelData()
        mDat = SparkClasses.SparkGeoData()
        levelData.geoData = mDat
        mDat.materialChunk = SparkClasses.SparkGeoMaterialChunk()
        mDat.vertexChunk = SparkClasses.SparkGeoVertexChunk()
        mDat.edgeChunk = SparkClasses.SparkGeoEdgeChunk()
        mDat.faceChunk = SparkClasses.SparkGeoFaceChunk()
        mDat.mappingChunk = SparkClasses.SparkGeoMappingGroupChunk()
        
        vC = mDat.vertexChunk
        vC.vertices = []
        
        for vert in me.vertices:
            sV = SparkClasses.SparkGeoVertex()
            if correct_axes:
                sV.x = vert.co[1]
                sV.y = vert.co[2]
                sV.z = vert.co[0]
            else:
                sV.x = vert.co[0]
                sV.y = vert.co[1]
                sV.z = vert.co[2]
            vC.vertices.append(sV)
        
        eC = mDat.edgeChunk
        eC.edges = []
        
        for edge in me.edges:
            sE = SparkClasses.SparkGeoEdge()
            sE.a = edge.vertices[0]
            sE.b = edge.vertices[1]
            sE.smooth = edge.use_edge_sharp
            eC.edges.append(sE)
        
        fC = mDat.faceChunk
        fC.faces = []
        
        for face in me.polygons:
            sF = SparkClasses.SparkGeoFace()
            if export_textures:
                tex = CalculateSparkTex(face, me, CORRECT_UNIT_FACTOR)
                sF.mapping = 0xFFFFFFFF
                if tex == None: #error during calculations, using defaults instead
                    sF.angle = 0.0
                    sF.xOffset = 0.0
                    sF.yOffset = 0.0
                    sF.xScale = 1.0
                    sF.yScale = 1.0
                    sF.material = AddMaterial("ns2/materials/dev/dev_1024x1024.dds",materials)
                else:
                    sF.angle = tex.angle
                    sF.xOffset = tex.xOffs
                    sF.yOffset = tex.yOffs
                    sF.xScale = tex.xScale
                    sF.yScale = tex.yScale
                    if not tex.image == None:
                        sF.material = AddMaterial(tex.image.filepath, materials)
                    else:
                        sF.material = AddMaterial("ns2/materials/dev/dev_1024x1024.dds",materials)
                
            else:
                sF.angle = 0.0
                sF.xOffset = 0.0
                sF.yOffset = 0.0
                sF.xScale = 1.0
                sF.yScale = 1.0
                sF.mapping = 0xFFFFFFFF
                sF.material = AddMaterial("ns2/materials/dev/dev_1024x1024.dds",materials)
                #print(sF.material)
            sF.innerLoops = []
            sF.borderLoop = SparkClasses.SparkGeoEdgeLoop()
            sF.borderLoop.edgeLoopMembers = []
            for loop in face.loop_indices:
                selm = SparkClasses.SparkGeoEdgeLoopMember()
                selm.edge = me.loops[loop].edge_index
                selm.flipped = True if me.edges[me.loops[loop].edge_index].vertices[1] == me.loops[loop].vertex_index else False
                sF.borderLoop.edgeLoopMembers.append(selm)
            fC.faces.append(sF)
            #print("material#: ",sF.material)
        
        matC = mDat.materialChunk #Simple matter of copying a list
        matC.materials=[]
        for material in materials:
            matC.materials.append(material)
        
        mapC = mDat.mappingChunk
        mapC.mappingGroups = [] #Currently not supporting the exporting of these mapping groups :(
        
        #Now, we merge the data with the existing data
        if mDatTotal == None:
            mDatTotal = mDat
        else:
            mDatTotal = SparkClasses.mergeSparkData(mDatTotal,mDat)
    
    if (mDatTotal == None):
        print("No mesh data to export to clipboard.  Aborting...")
        raise SparkClasses.SparkError("No mesh data to export, aborting...")
    else:
        writer = SparkClasses.SparkWriter()
        bData = mDatTotal.convertToBinString()
        ClipUtils.SetClipboardFromString(bData)
    materials = []
