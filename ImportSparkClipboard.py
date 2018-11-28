# Written by Trevor Harris aka BeigeAlert.
# Feel free to modify at your leisure, just make sure you
# give credit where it's due.
# Cheers! -Beige
# Last modified November 28, 2018

import bpy
import os
from . import SparkClasses
from . import ClipUtils
import bmesh
from . import Triangulation
import math
from mathutils import Vector
from mathutils import Euler

validPaths = []

def INCHESPERMETER(): return 39.3700787

class MaterialGrouping:
    '''Just a small class to hold the potential maps as they are read-in'''
    def __init__(self):
        self.name = None
        self.albedoMap = None
        self.normalMap = None
        self.specularMap = None
        self.opacityMap = None
        self.emissiveMap = None


def FixPath(path):
    if path == None:
        return None
    if path == '':
        return ''
    path = path.replace('\\','/')
    
    if path[-1] != '/':
        path = path + '/'
    return path.replace('\\','/')


def AddTexture(tex, textures):
    if not tex == None:
        img = bpy.data.images.load(tex)
        img.use_alpha = False
        textures.append(img)
    else:
        textures.append(None)


def GetCleanTextureName(tex):
    '''Strips the folders off the front of the file path, leaving just the name and the extension, then
    strips the extension off, preserving any extra dots that some idiot may have put into the filename.
    In other words, it strips off everything before the filename, and everything after the last dot.'''
    return '.'.join(tex.split('/')[-1].split('.')[:-1])


def AddDummyMaterial():
    mat = bpy.data.materials.new("dummy_material")
    mat.emit = 0.5
    return mat

def AddMaterial(mGrouping):
    '''Returns a material from the textures provided, and returns it, or returns an
    existing material if the name matches the path'''
    #Check to see if material is 'None', in which case it's a dummy material.
    if (mGrouping == None):
        return AddDummyMaterial()
    #Check to see if this material already exists in the .blend file.
    index = bpy.data.materials.find(mGrouping.name)
    if index == -1: #Not found, need to make a new material
        mat = bpy.data.materials.new(mGrouping.name) #Create a new material named after the .material file's full path.
        albedoTex = None #Keeping a reference out of scope just for the albedo because on some textures, the spec map is
                         #the albedo's alpha channel.
        containsTransparency = False
        if not mGrouping.albedoMap == None:
            if not mGrouping.albedoMap == '': #If there's an albedoMap present, create a texture for it.
                albedoTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.albedoMap), 'IMAGE' )
                albedoTex.image = bpy.data.images.load(mGrouping.albedoMap)
                albedoTex.image.use_alpha = False
                texSlot = mat.texture_slots.add()
                texSlot.texture = albedoTex
                texSlot.use_map_color_diffuse = True
                texSlot.diffuse_color_factor = 1.0
                texSlot.texture_coords = 'UV'
        if not mGrouping.normalMap == None:
            if not mGrouping.normalMap == '': #If there's a normalMap preset, create a texture for it.
                normalTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.normalMap), 'IMAGE' )
                normalTex.image = bpy.data.images.load(mGrouping.normalMap)
                normalTex.use_normal_map = True
                normalTex.image.use_alpha = False
                texSlot = mat.texture_slots.add()
                texSlot.texture = normalTex
                texSlot.normal_map_space = 'TANGENT'
                texSlot.use_map_normal = True
                texSlot.use_map_color_diffuse = False
                texSlot.normal_factor = 1.0
                texSlot.texture_coords = 'UV'
        specularMapFound = False
        if not mGrouping.specularMap == None:
            if not mGrouping.specularMap == '': #If there's a specularMap present, create a texture for it.
                specularTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.specularMap), 'IMAGE' )
                specularTex.image = bpy.data.images.load(mGrouping.specularMap)
                specularTex.image.use_alpha = False #Don't want to use the alpha, that's the gloss channel
                texSlot = mat.texture_slots.add()
                texSlot.texture = specularTex
                texSlot.use_map_color_spec = True
                texSlot.use_map_color_diffuse = False
                texSlot.specular_color_factor = 1.0
                texSlot.texture_coords = 'UV'
                specularMapFound = True
                if (specularTex.image.channels == 4): #Gloss channel on this needs a new texture
                    glossTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.specularMap) + '_gloss', 'IMAGE')
                    glossTex.image = bpy.data.images.load(mGrouping.specularMap)
                    glossTex.use_alpha = True
                    texSlotG = mat.texture_slots.add()
                    texSlotG.texture = glossTex
                    texSlotG.use_map_hardness = True
                    texSlotG.use_map_color_diffuse = False
                    texSlotG.hardness_factor = 1.0
                    texSlotG.texture_coords = 'UV'
        if not specularMapFound:
            #Didn't locate a dedicated specular map.  Need to check to see if this is one of those materials
            #where they've made the albedo map's alpha channel into a greyscale specular map.
            if not albedoTex == None:
                if (albedoTex.image.channels == 4): #4th channel is alpha
                    specularTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.albedoMap) + '_spec', 'IMAGE')
                    specularTex.image = bpy.data.images.load(mGrouping.albedoMap)
                    specularTex.use_alpha = True
                    texSlot = mat.texture_slots.add()
                    texSlot.texture = specularTex
                    texSlot.use_map_specular = True
                    texSlot.use_map_color_diffuse = False
                    texSlot.specular_factor = 1.0
                    texSlot.texture_coords = 'UV'
        if not mGrouping.opacityMap == None: #If there's an opacityMap present, create a texture for it.
            if not mGrouping.opacityMap == '':
                opacityTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.opacityMap), 'IMAGE' )
                opacityTex.image = bpy.data.images.load(mGrouping.opacityMap)
                opacityTex.image.use_alpha = False
                texSlot = mat.texture_slots.add()
                texSlot.texture = opacityTex
                texSlot.use_map_alpha = True
                texSlot.use_map_color_diffuse = False
                texSlot.alpha_factor = 1.0
                texSlot.use_rgb_to_intensity = True
                texSlot.texture_coords = 'UV'
                containsTransparency = True
        if not mGrouping.emissiveMap == None: #If there's an emissiveMap present, create a texture for it.
            if not mGrouping.emissiveMap == '':
                emissiveTex = bpy.data.textures.new(GetCleanTextureName(mGrouping.emissiveMap), 'IMAGE' )
                emissiveTex.image = bpy.data.images.load(mGrouping.emissiveMap)
                emissiveTex.image.use_alpha = False
                texSlot = mat.texture_slots.add()
                texSlot.texture = emissiveTex
                texSlot.use_map_emit = True
                texSlot.use_map_color_diffuse = False
                texSlot.emit_factor = 1.0
                texSlot.blend_type = 'ADD'
                texSlot.use_rgb_to_intensity = True
        mat.diffuse_color = (1.0,1.0,1.0)
        mat.diffuse_intensity = 1.0
        mat.specular_intensity = 1.0
        mat.specular_color = (1.0,1.0,1.0)
        mat.specular_hardness = 60
        mat.emit = 0.5
        if containsTransparency:
            mat.use_transparency = True
            mat.alpha = 0.0
        return mat
    else: #Material already exists, return existing copy
        return bpy.data.materials[index]


def IsPathValid(dir):
    return os.path.isdir(dir)


def DoesFileExist(file):
    return os.path.isfile(file)

    
def LocateSuitableTexture(mGroup, path):
    #loop through each of these 5 variables, sorted by priority.  This is the texture that will be used for the
    #UV map background, and all the calculations.
    maps = [mGroup.albedoMap, mGroup.emissiveMap, mGroup.normalMap, mGroup.opacityMap, mGroup.specularMap ]
    for map in maps:
        if not map == None:
            if not map == '':
                tex = map
                if DoesFileExist(tex):
                    return tex
    return None #This ain't good!
    
def ReadMaterialFile(file, path):
    '''knownMaps = ['albedomap','normalmap','specularmap','opacitymap','emissivemap']'''
    mGrouping = MaterialGrouping()
    mGrouping.name = GetCleanTextureName(file)
    f = open(file, 'r')
    mLine = []
    for line in f:
        mLine.append(line.strip().lower())
    
    for line in mLine:
        if (line.startswith("albedomap")):
            mGrouping.albedoMap = path + line.split('"')[1]
        elif (line.startswith("normalmap")):
            mGrouping.normalMap = path + line.split('"')[1]
        elif (line.startswith("specularmap")):
            mGrouping.specularMap = path + line.split('"')[1]
        elif (line.startswith("opacitymap")):
            mGrouping.opacityMap = path + line.split('"')[1]
        elif (line.startswith("emissivemap")):
            mGrouping.emissiveMap = path + line.split('"')[1]
    
    return mGrouping
    
    
def calcMagnitude(vec):
    """Returns the magnitude of a vector, can be any number of dimensions"""
    mag = 0.0
    for d in vec:
        mag+= d*d
    return math.sqrt(mag)


def cross(a,b):
    """Taken from http://stackoverflow.com/questions/1984799/cross-product-of-2-different-vectors-in-python"""
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]
    return c


def CalculateNormal(v1,v2,v3):
    vec1 = ( v2.x-v1.x , v2.y-v1.y , v2.z-v1.z )
    vec2 = ( v3.x-v1.x , v3.y-v1.y , v3.z-v1.z )
    norm = cross(vec1,vec2)
    if (abs(norm[0]) < 0.00001) and (abs(norm[1]) < 0.00001) and (abs(norm[2]) < 0.00001):
        return None #failed: the vertex formed a PERFECT 180 degree angle, therefore normal cannot be derived from these vectors
    mag = calcMagnitude(norm)
    return ( norm[0]/mag , norm[1]/mag , norm[2]/mag )

def CalculateVertUVCoord(vertex, normalVector, texSettings, CORRECT_UNIT_FACTOR, textures):
    angle = texSettings[0]
    xOffset = texSettings[1]*-1
    yOffset = texSettings[2]*-1
    xScale = texSettings[3]
    yScale = texSettings[4]
    material = texSettings[5]
    texDim = (512, 512) #default value, if no texture is found
    try:
        if (textures[material] != None):
            texDim = textures[material].size
    except IndexError:
        pass
    
    norm = [normalVector[0], normalVector[1], normalVector[2]]
    
    #Correct the scaling values back to being in terms of image size, not meters.  Spark stores the scale
    #in meters in the clipboard (scale value from editor = 39.37 * 8 / image dimensions)
    xScale = (8*CORRECT_UNIT_FACTOR) / (xScale * texDim[0])
    yScale = (8*CORRECT_UNIT_FACTOR) / (yScale * texDim[1])
    
    # First, we need to rotate the coordinates for this vertex around the world origin
    # to get it into the proper texture space.  I'm no good at this kind of math... so
    # uh... buckle up if you're reading this.  Things are about to get rocky.
    texCoords = []
    texCoords.append(vertex.co[0])
    texCoords.append(vertex.co[1])
    texCoords.append(vertex.co[2])
    
    norm[0]*=-1
    norm[1]*=-1
    norm[2]*=-1
    
    #Allowing a 0.00127 margin of error for something being "flat" or not.  This is very close to spark's actual tolerance.
    if ( abs( norm[0] ) < 0.00127 ) and ( abs( norm[1] ) < 0.00127 ) and (  norm[2] >= -0.99873 ):
        #Normal is close enough to straight up
        norm[0] = 0.0
        norm[1] = 0.0
        norm[2] = 1.0
    elif ( abs( norm[0] ) < 0.00127 ) and ( abs( norm[1] ) < 0.00127 ) and (  norm[2] <= 0.99873 ):
        #Normal is close enough to straight down.  We'll just flip it.
        norm[0] = 0.0
        norm[1] = 0.0
        norm[2] = 1.0
        texCoords[0] = texCoords[0]*-1
        texCoords[1] = texCoords[1]*-1
        texCoords[2] = texCoords[2]*-1
    else:
        a = math.pi - math.atan2( norm[0] , norm[1] ) #Z rotation of normal
        x = texCoords[0] * math.cos(-a) - texCoords[1] * math.sin(-a)
        y = texCoords[0] * math.sin(-a) + texCoords[1] * math.cos(-a)
        texCoords[0] = x
        texCoords[1] = y
        norm[1] = math.sqrt( ( norm[0]*norm[0] ) + ( norm[1]*norm[1] ) )
        norm[0] = 0.0
        
        #Now we'll deal with the pitch (y axis)
        a = -math.atan2( norm[1], norm[2] )
        texCoords[1] = texCoords[1] * math.cos(a) - texCoords[2] * math.sin(a)
    
    #Now we need to rotate it once more around the z axis to cancel out the face's "angle"
    #We have to take into account the texture's aspect ratio as well because it'll have to skew when it rotates
    #aspect = texDim[0]/texDim[1]
    #texCoords[1] = texCoords[1] * aspect
    x = texCoords[0] * math.cos(angle) - texCoords[1] * math.sin(angle)
    y = texCoords[0] * math.sin(angle) + texCoords[1] * math.cos(angle)
    texCoords[0] = x
    texCoords[1] = y#/aspect
    
    #Now the polygon should be completely flat, save for any minor imperfections due
    #to >3 sided polygons never being technically 100% planar
    #Okay, now we should be good to start calculating where this vertex lies in UV-space
    texCoords[0] = (((texCoords[0] * 8) / (texDim[0] * xScale)) - xOffset)
    texCoords[1] = (((texCoords[1] * 8) / (texDim[1] * yScale)) + yOffset)
    
    texCoords=texCoords[:2] #We don't need that 3rd dimension anymore
    return texCoords

    
def MapUVsFromSparkTex(bm, bface, normalVector, texSettings, CORRECT_UNIT_FACTOR, textures):
    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.tex.verify()
    
    bm.faces.layers.tex.verify()
    bm.faces.ensure_lookup_table()
    for l in bm.faces[bface].loops:
        luv = l[uv_layer]
        co = CalculateVertUVCoord(l.vert, normalVector, texSettings, CORRECT_UNIT_FACTOR, textures)
        luv.uv = co


def LoadMaterial(texPaths, mat, textures):
    for path in texPaths:
        file = path + mat
        if DoesFileExist(file):
            mGrouping = ReadMaterialFile(file,path)
            tex = LocateSuitableTexture(mGrouping, path)
            if not tex == None: #Can only fail if NONE of the textures from the .material file can be located
                AddTexture(tex, textures)
                mat = AddMaterial(mGrouping)
                return mat
    AddTexture(None, textures)
    return AddMaterial(None)


def FindMeshDataForStaticProp(relativeFilePath):
    for mesh in bpy.data.meshes:
        if 'SparkFilePath' in mesh and mesh['SparkFilePath'] == relativeFilePath:
            return mesh
    return None


class BaseVert:
    def __init__(self, pos):
        self.pos = pos
        self.loops = []
    
    def __eq__(self, other):
        return type(self) == type(other) and self.pos.x == other.pos.x and self.pos.y == other.pos.y and self.pos.z == other.pos.z
    
    def __hash__(self):
        return hash((self.pos.x, self.pos.y, self.pos.z))


class LoopVert:
    def __init__(self, baseVert, nrm, tan, bit, uv):
        self.baseVert = baseVert
        self.nrm = nrm
        self.tan = tan
        self.bit = bit
        self.uv = uv
    
    def __eq__(self, other):
        return type(self) == type(other) and self.baseVert == other.baseVert and self.nrm.x == other.nrm.x and self.nrm.y == other.nrm.y and self.nrm.z == other.nrm.z and self.tan.x == other.tan.x and self.tan.y == other.tan.y and self.tan.z == other.tan.z and self.bit.x == other.bit.x and self.bit.y == other.bit.y and self.bit.z == other.bit.z and self.uv.x == other.uv.x and self.uv.y == other.uv.y
    
    def __hash__(self):
        return hash((self.baseVert, self.nrm.x, self.nrm.y, self.nrm.z, self.tan.x, self.tan.y, self.tan.z, self.bit.x, self.bit.y, self.bit.z, self.uv.x, self.uv.y))


def CycleVector(vec3):
    return Vector((vec3.z, vec3.x, vec3.y))


def FlipVector(vec2):
    return Vector((vec2.x, 1.0 - vec2.y))


def CreateMeshForSparkModel(model):
    
    mesh = bpy.data.meshes.new("StaticPropMesh")
    
    baseVertSet = {}
    loopVertSet = {}
    baseVertList = []
    loopVertList = []
    inputIndexToLoopVertMap = []
    
    for inputVert in model.vertices:
        baseVert = BaseVert(inputVert.pos)
        if baseVert in baseVertSet:
            baseVert = baseVertList[baseVertSet[baseVert]]
        else:
            baseVertSet[baseVert] = len(baseVertList)
            baseVertList.append(baseVert)
        
        loopVert = LoopVert(baseVert, inputVert.nrm, inputVert.tan, inputVert.bit, inputVert.uv)
        if loopVert in loopVertSet:
            loopVert = loopVertList[loopVertSet[loopVert]]
        else:
            loopVertSet[loopVert] = len(loopVertList)
            loopVertList.append(loopVert)
        
        inputIndexToLoopVertMap.append(loopVert)
    
    mesh.vertices.add(len(baseVertList))
    for i, bv in enumerate(baseVertList):
        mesh.vertices[i].co = Vector((bv.pos.z, bv.pos.x, bv.pos.y))
    
    mesh.loops.add(len(model.indices))
    mesh.uv_textures.new()
    uv_layer = mesh.uv_layers[0]
    custom_normals = [None] * len(model.indices)
    for i in range(len(model.indices) // 3):
        for j in range(3):
            mesh.loops[i*3+j].vertex_index = baseVertSet[inputIndexToLoopVertMap[model.indices[i*3+j]].baseVert]
            uv_layer.data[i*3+j].uv = FlipVector(inputIndexToLoopVertMap[model.indices[i*3+j]].uv)
            custom_normals[i*3+j] = CycleVector(inputIndexToLoopVertMap[model.indices[i*3+j]].nrm)
    
    mesh.polygons.add(len(model.indices) // 3)
    for i in range(len(model.indices) // 3):
        mesh.polygons[i].loop_start = i*3
        mesh.polygons[i].loop_total = 3
    
    for faceSet in model.faceSets:
        for j in range(faceSet.firstFaceIndex, faceSet.firstFaceIndex + faceSet.faceCount):
            mesh.polygons[i].material_index = faceSet.materialIndex
    
    mesh.update(calc_edges=True)
    mesh.normals_split_custom_set(custom_normals)
    mesh.use_auto_smooth = True
    
    return mesh


def LoadMeshDataForStaticProp(relativeFilePath):
    
    for path in validPaths:
        file = path + relativeFilePath
        
        if DoesFileExist(file):
            file_read = open(file, 'rb')
            data = file_read.read()
            file_read.close()
            reader = SparkClasses.SparkReader(data)
            model = SparkClasses.SparkModel().readData(reader)
            mesh = CreateMeshForSparkModel(model)
            mesh['SparkFilePath'] = relativeFilePath
            return mesh


def GetMeshDataForStaticProp(relativeFilePath):
    
    meshData = FindMeshDataForStaticProp(relativeFilePath)
    if meshData != None:
        return meshData
    
    return LoadMeshDataForStaticProp(relativeFilePath)


def AddProp(prop, correct_units):
    
    objData = GetMeshDataForStaticProp(prop.modelFilePath)
    if objData == None:
        print("no data")
        return
    
    obj = bpy.data.objects.new("StaticProp", objData)
    bpy.context.scene.objects.link(obj)
    
    # add materials
    # TODO bit of a scope issue here... materials are loaded with the mesh... which isn't known at the object level :/
    
    # orient the object
    sceneScale = INCHESPERMETER() if correct_units else 1.0
    
    obj.location = CycleVector(prop.origin) * sceneScale
    obj.rotation_euler = Euler(prop.angles, 'XYZ')
    obj.scale = CycleVector(prop.scale) * sceneScale


def ImportClipboardData(operator, context,
        correct_units = True,
        correct_axes = True,
        import_textures = True,
        tex_dir_1 = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Natural Selection 2\\ns2\\",
        tex_dir_2 = "",
        tex_dir_3 = "",
        tex_dir_4 = "",
        tex_dir_5 = "",
        ):
    """Imports the clipboard data, and creates all the necessary objects"""
    validPaths.clear()
    
    textures = []   ### The texture indices in this list should line up perfectly with the imported material indices.
                    ### Be sure to do None checks when using this list, as textures that cannot be located are still
                    ### added to the list as None to preserve the material indices.
                    
    bMats = []      ### List of blender materials that corresponds to the imported materials list.
    tex_dir_1 = FixPath(tex_dir_1) #replace all backslashes with forward slashes... because spark gets to have it's way...
    tex_dir_2 = FixPath(tex_dir_2)
    tex_dir_3 = FixPath(tex_dir_3)
    tex_dir_4 = FixPath(tex_dir_4)
    tex_dir_5 = FixPath(tex_dir_5)
    
    if (IsPathValid(tex_dir_1)):
        validPaths.append(tex_dir_1)
    if (IsPathValid(tex_dir_2)):
        validPaths.append(tex_dir_2)
    if (IsPathValid(tex_dir_3)):
        validPaths.append(tex_dir_3)
    if (IsPathValid(tex_dir_4)):
        validPaths.append(tex_dir_4)
    if (IsPathValid(tex_dir_5)):
        validPaths.append(tex_dir_5)
        
    if (validPaths == None or validPaths == []):
        import_textures = False
        print("WARNING: None of the texture paths are valid.  Switching texture import off.")
    data = ClipUtils.GetClipboardAsString()
    sparkData = SparkClasses.SparkLevelData().readData(data)
    
    if sparkData.geoData:
        
        ### Import Materials ###
        if (import_textures):
            for material in sparkData.geoData.materialChunk.materials:
                b = LoadMaterial(validPaths, material, textures)
                bMats.append(b)
                if b == None:
                    print("WARNING: Unable to locate texture file for \"", material, "\".  UVs may be distorted!")
        
        ### Import Vertices ###
        bm = bmesh.new()
        verts = []
        CORRECT_UNIT_FACTOR = 1.0
        if correct_units:
            CORRECT_UNIT_FACTOR = INCHESPERMETER()
        for vertex in sparkData.geoData.vertexChunk.vertices:
            if correct_axes:
                verts.append(bm.verts.new((vertex.z*CORRECT_UNIT_FACTOR,vertex.x*CORRECT_UNIT_FACTOR,vertex.y*CORRECT_UNIT_FACTOR)))
            else:
                verts.append(bm.verts.new((vertex.x*CORRECT_UNIT_FACTOR,vertex.y*CORRECT_UNIT_FACTOR,vertex.z*CORRECT_UNIT_FACTOR)))
        
        ### Import Edges ###
        edges = []
        for edge in sparkData.geoData.edgeChunk.edges:
            edges.append( edge )
        
        ### Import Faces ###
        polys = []
        tex_layer = bm.faces.layers.tex.verify()
        for faceIndex, face in enumerate(sparkData.geoData.faceChunk.faces):
            normalVector = None
            texSettings = None
            if (face.mappingIdx == 0xFFFFFFFF):
                #No mapping group applied, therefore we just go ahead and use the face's mapping settings
                texSettings = (face.angle, face.xOffset, face.yOffset, face.xScale, face.yScale, face.materialIdx)
            else:
                mappingIndex = sparkData.geoData.mappingChunk.getMappingById(face.mappingIdx)
                if (mappingIndex == -1):
                    #Mapping group doesn't exist, just go ahead and use the face normals
                    texSettings = (face.angle, face.xOffset, face.yOffset, face.xScale, face.yScale, face.materialIdx)
                else:
                    map = sparkData.geoData.mappingChunk.mappingGroups[mappingIndex]
                    normalVector = [map.zNormal, map.xNormal, map.yNormal]
                    texSettings = (map.angle, map.xOffset, map.yOffset, map.xScale, map.yScale, face.materialIdx)
            
            f = []
            if (face.innerLoops == None or face.innerLoops == [] or face.innerLoops[0].edgeLoopMembers == []):
                # It's a polygon with no holes, hot damn!
                v = [] #verts just for this face
                
                for loopM in face.borderLoop.edgeLoopMembers:
                    bm.verts.ensure_lookup_table()
                    v.append(bm.verts[edges[loopM.edgeIdx].idxB] if loopM.flipped else bm.verts[edges[loopM.edgeIdx].idxA])
                
                #Do a quick check to ensure this face doesn't have double verts.
                faceValid = True
                for vertIndex in range(0,len(v)):
                    if v.count(v[vertIndex]) != 1:
                        faceValid = False
                        break
                if not faceValid:
                    print("WARNING: Skipping face", faceIndex, "as it contained duplicate vertices")
                    continue #skips this face and moves on to the next face.
                try:
                    bmf = bm.faces.new(v)
                except ValueError:
                    print("WARNING: Error creating face", faceIndex, ", skipping...")
                    continue
                except TypeError:
                    continue
                f.append(bmf)
                if normalVector == None:
                    #Calculate the normal from the first 3 vertices in the list.  BUT, in the unlikely, but still very
                    #possible event that the 3 vertices selected are inline (ie: a perfect 180 degree angle is formed,
                    #and therefore the normal cannot be derived from those 3 points), we move down the list one vertex
                    #and try again.  Eventually, we'll reach a vertex triplet that will work.  If we don't, just move
                    #on to the next face.
                    foundNonCollinear = False
                    for i in range(0,len(v)):
                        normalVector = CalculateNormal( v[i].co , v[(i+len(v)-1)%len(v)].co , v[(i+1)%len(v)].co )
                        if not normalVector == None:
                            foundNonCollinear = True
                            break
                    if not foundNonCollinear: #this only happens if the face is made of colinear vertices; an invalid face.
                        #Valid face cannot be formed, delete the face that was just added.
                        bm.faces.remove(bmf)
                        continue
                MapUVsFromSparkTex(bm, bmf.index, normalVector, texSettings, CORRECT_UNIT_FACTOR, textures)
                try:
                    bm.faces[bmf.index][tex_layer].image=textures[texSettings[5]]
                except IndexError:
                    pass
                bm.faces[bmf.index].material_index = texSettings[5]
            else:
                p = Triangulation.polygon(face, sparkData.geoData)
                polys.append( p )
                norm = None
                for triangle in p.triangles:
                    v1 = verts[triangle.v1.realId]
                    v2 = verts[triangle.v2.realId]
                    v3 = verts[triangle.v3.realId]
                    if normalVector == None:
                        normalVector = CalculateNormal( v1.co , v2.co , v3.co )
                    try:
                        bmf = bm.faces.new((v1,v2,v3))
                    except ValueError:
                        continue
                    f.append(bmf)
                    MapUVsFromSparkTex(bm, bmf.index, normalVector, texSettings, CORRECT_UNIT_FACTOR, textures)
                    try:
                        bm.faces[bmf.index][tex_layer].image=textures[texSettings[5]]
                    except IndexError:
                        pass
                    bm.faces[bmf.index].material_index = texSettings[5]
        #Now we need to go through and ensure that edges that were marked as smooth are now set as "sharp" in Blender.
        #Yea it's a bit odd, but that's the only analog I could find that worked suitably well.  Unfortunately, there's
        #no guarantee that the edges indices will line up from one mesh format to the other as new edges are created
        #automatically by bmesh when the polygons are created.  Therefore we must loop through every spark edge and when
        #we find a 'smooth' edge, we'll need to search through every bmesh edge for the match, and then set that to sharp.
        bm.verts.index_update()
        for sEdge in edges:
            if (sEdge.smooth):
                for bEdge in bm.edges:
                    if (bEdge.verts[0].index == sEdge.a) and (bEdge.verts[1].index == sEdge.b):
                        bEdge.smooth = False
                    elif (bEdge.verts[0].index == sEdge.b) and (bEdge.verts[1].index == sEdge.a):
                        bEdge.smooth = False
        
        #That should be it!  Just need to convert it back to a mesh from the bmesh module.
        
        mesh = bpy.data.meshes.new("ImportedSparkMesh")
        bm.to_mesh(mesh)
        bm.free()
        scene = bpy.context.scene
        obj = bpy.data.objects.new("ImportedSparkMeshObject", mesh)
        me = obj.data
        for bmat in bMats:
            me.materials.append(bmat)
        scene.objects.link(obj)
        textures = []
    
    # Import props now
    if sparkData.entityData:
        for prop in sparkData.entityData.staticProps:
            AddProp(prop, correct_units)
    
    