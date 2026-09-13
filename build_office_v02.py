import bpy, math, random, os
from mathutils import Vector
from math import sin, cos, pi
random.seed(27)
ROOT = '/Users/alphaone/Blender3D-MCP'

# PHASE 1: editable scene, materials, architecture, camera
scene = bpy.data.scenes.new('WEER Studio • Reference rebuild')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene['reference'] = 'Codex Image Sep 13, 2026, 01_16_04 PM.png'
scene['dimensions'] = 'Floor 3.5 x 3.5 m; remaining dimensions estimated from reference'
collections = {}
def group(name):
    global current
    if name not in collections:
        c = bpy.data.collections.new(name); scene.collection.children.link(c); collections[name] = c
    current = collections[name]
def link(o, name, material=None):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    current.objects.link(o)
    if material: o.data.materials.append(material)
    return o
def material(name, color, rough=.5, metal=0, noise=0, scale=50, emission=0):
    m=bpy.data.materials.new('V02 • '+name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; bs=n.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1); bs.inputs['Emission Strength'].default_value=emission
    if noise:
        tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale; tex.inputs['Detail'].default_value=3
        ramp=n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.2; ramp.color_ramp.elements[0].color=(*(v*(1-noise) for v in color),1)
        ramp.color_ramp.elements[1].position=.8; ramp.color_ramp.elements[1].color=(*(min(1,v*(1+noise)) for v in color),1)
        l.new(tex.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.25; bump.inputs['Distance'].default_value=.018 if scale<30 else .002
        l.new(tex.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],bs.inputs['Normal'])
    return m
white=material('warm white enamel',(.84,.85,.83),.32)
ivory=material('door ivory',(.72,.73,.71),.48)
concrete=material('cast concrete',(.34,.36,.38),.85,noise=.23,scale=8)
edge=material('slate cut edges',(.105,.13,.155),.6,noise=.10,scale=30)
black=material('charcoal black',(.018,.023,.027),.4)
silver=material('satin aluminium',(.48,.53,.55),.3,.65)
blue=material('petrol blue panels',(.008,.25,.39),.36,noise=.10,scale=20)
led=material('cyan LED',(.02,.65,1),.25,emission=5)
warmled=material('warm halo', (1,.64,.25),.35,emission=5)
paper=material('art paper',(.8,.79,.73),.9)
rug=material('blue grey woven rug',(.28,.40,.50),.98,noise=.4,scale=220)
cloth=material('grey upholstery',(.32,.34,.35),.98,noise=.26,scale=160)
meshmat=material('mesh threads',(.53,.55,.53),.72)
soil=material('soil',(.055,.038,.023),1,noise=.4,scale=60)
potmat=material('speckled stoneware',(.65,.66,.61),.8,noise=.4,scale=90)
leafmats=[material('foliage '+str(i),c,.46,noise=.18,scale=8) for i,c in enumerate([(.07,.22,.026),(.15,.32,.045),(.035,.14,.035),(.23,.36,.07)])]
woodmats=[]
for i in range(9):
    m=material('oak plank '+str(i),(.42+i*.016,.235+i*.012,.11+i*.007),.46,noise=.28,scale=4)
    ns=m.node_tree.nodes; ls=m.node_tree.links; tex=next(n for n in ns if n.type=='TEX_NOISE')
    coord=ns.new('ShaderNodeTexCoord'); mapping=ns.new('ShaderNodeVectorMath'); mapping.operation='MULTIPLY'; mapping.inputs[1].default_value=(2,65,5)
    ls.new(coord.outputs['Generated'],mapping.inputs[0]); ls.new(mapping.outputs[0],tex.inputs['Vector']); woodmats.append(m)
bamboomats=[material('bamboo '+str(i),(.38+i*.025,.23+i*.016,.095+i*.01),.46,noise=.17,scale=8) for i in range(5)]
def cube(name,loc,dims,mat,bevel=.008,rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=link(bpy.context.object,name,mat); o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rotation: o.rotation_euler=rotation
    if bevel:
        b=o.modifiers.new('edge radii','BEVEL'); b.width=bevel; b.segments=3
        n=o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return o
def uv(name,loc,scale,mat,segments=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc)
    o=link(bpy.context.object,name,mat); o.scale=scale
    for p in o.data.polygons: p.use_smooth=True
    return o
def cyl(name,loc,r,depth,mat,r2=None,rotation=None,verts=32):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc)
    else: bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r2,depth=depth,location=loc)
    o=link(bpy.context.object,name,mat)
    if rotation: o.rotation_euler=rotation
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    b=o.modifiers.new('rim radii','BEVEL'); b.width=.002; b.segments=2
    return o
def tube(name,points,r,mat,closed=False):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=2
    sp=cu.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points): p.co=(*co,1)
    sp.use_cyclic_u=closed; o=bpy.data.objects.new(name,cu); current.objects.link(o); cu.materials.append(mat); return o
def rod(name,a,b,r,mat):
    a,b=Vector(a),Vector(b); o=cyl(name,(a+b)/2,r,(b-a).length,mat)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return o
def text(name,body,loc,size,mat,rot=(pi/2,0,0),extrude=.001):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.size=size; cu.align_x='CENTER'; cu.align_y='CENTER'; cu.extrude=extrude; cu.bevel_depth=.0005
    o=bpy.data.objects.new(name,cu); current.objects.link(o); o.location=loc; o.rotation_euler=rot; cu.materials.append(mat); return o
def aim(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target):
    da=bpy.data.lights.new(name,'AREA'); da.energy=power; da.color=color; da.shape='DISK'; da.size=size
    o=bpy.data.objects.new(name,da); current.objects.link(o); o.location=loc; aim(o,target); return o

group('01 Architecture')
cube('3.5m square floor foundation',(0,0,-.085),(3.64,3.64,.17),edge,.012)
for row in range(20):
    y=-1.75+(row+.5)*.175
    start=-1.75
    cuts=[-1.75]+[v for v in [-2.1+(row%3)*.34+j*1.04 for j in range(6)] if -1.73<v<1.73]+[1.75]
    for j,(a,b) in enumerate(zip(cuts,cuts[1:])):
        cube('Oak staggered plank %02d-%d'%(row,j),((a+b)/2,y,.008),(b-a-.002,.173,.016),random.choice(woodmats),.001)
# Left wall is x=-1.80. Window is a true opening.
cube('Left wall door and pegboard section',(-1.8,-.82,1.36),(.12,1.86,2.72),concrete,.003)
cube('Left wall rear pier',(-1.8,1.635,1.36),(.12,.23,2.72),concrete,.003)
cube('Left window sill wall',(-1.8,.815,.08),(.12,1.41,.16),concrete,.002)
cube('Left window lintel',(-1.8,.815,2.64),(.12,1.41,.16),concrete,.003)
cube('Logo wall',(0,1.8,1.36),(3.72,.12,2.72),concrete,.004)
cube('Top left dark coping',(-1.8,0,2.735),(.16,3.65,.045),edge,.003)
cube('Top back dark coping',(0,1.8,2.735),(3.72,.16,.045),edge,.003)
for x,y in [(-1.81,-1.78),(1.80,1.80)]: cube('Cut wall vertical edge',(x,y,1.36),(.14,.14,2.74),edge,.003)
cube('Front low cut edge',(0,-1.79,.065),(3.64,.10,.13),edge,.004)
cube('Right low cut edge',(1.79,0,.065),(.10,3.64,.13),edge,.004)
cube('Back skirting',(0,1.722,.075),(3.5,.022,.15),ivory,.002)
cube('Left skirting',(-1.722,-.81,.075),(.022,1.86,.15),ivory,.002)

group('02 Door and window')
cube('Door slab',(-1.722,-1.24,1.055),(.038,.79,2.07),ivory,.005)
for y in [-1.675,-.805]: cube('Door jamb',(-1.687,y,1.08),(.052,.055,2.16),white,.004)
cube('Door header',(-1.687,-1.24,2.16),(.052,.92,.055),white,.004)
for z in [.17,1.94]: cube('Door recessed border',(-1.699,-1.24,z),(.009,.63,.009),paper,.001)
for y in [-1.55,-.93]: cube('Door recessed border',(-1.699,y,1.055),(.009,.009,1.77),paper,.001)
cube('Door handle plate',(-1.675,-.96,1.0),(.020,.044,.145),black,.007)
rod('Door lever',(-1.64,-.96,1.0),(-1.64,-1.08,1.0),.013,black)
cube('Doormat',(-1.32,-1.27,.026),(.58,.76,.018),cloth,.012)
for y in [-.745,-.69]:
    cube('Switch socket plate',(-1.718,y,.97),(.018,.035,.11),black,.003)
    cube('Switch insert',(-1.705,y,.98),(.008,.019,.045),silver,.001)
for y in [.105,.82,1.525]: cube('Window vertical mullion',(-1.746,y,1.35),(.075,.035,2.4),black,.004)
for z in [.16,.83,2.54]: cube('Window crossbar',(-1.746,.815,z),(.075,1.455,.035),black,.004)
# Foliage beyond the glazing: soft procedural green/light pattern.
outside=material('out of focus outdoor foliage',(.55,.68,.34),.8,emission=.65)
ns=outside.node_tree.nodes; ls=outside.node_tree.links; bs=ns.get('Principled BSDF')
no=ns.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value=7; no.inputs['Detail'].default_value=1
ra=ns.new('ShaderNodeValToRGB'); ra.color_ramp.elements[0].position=.28; ra.color_ramp.elements[0].color=(.12,.24,.055,1)
ra.color_ramp.elements[1].position=.68; ra.color_ramp.elements[1].color=(.86,.94,.87,1)
ls.new(no.outputs['Fac'],ra.inputs[0]); ls.new(ra.outputs[0],bs.inputs['Base Color']); ls.new(ra.outputs[0],bs.inputs['Emission Color'])
cube('Soft garden beyond window',(-1.91,.815,1.35),(.012,1.44,2.38),outside,0)
cube('Blind headbox',(-1.682,.815,2.53),(.13,1.51,.12),edge,.006)
for i in range(15):
    cube('Venetian blind slat %02d'%i,(-1.68,.815,2.43-i*.068),(.095,1.40,.021),edge,.002,rotation=(0,.20,0))
for y in [.40,1.2]: cube('Blind tape',(-1.624,y,1.975),(.009,.022,1.00),black,.001)

group('03 Feature wall')
for x,w in [(-1.40,.45),(1.13,.75)]:
    cube('Petrol blue vertical inset',(x,1.728,1.40),(w,.022,2.54),blue,.001)
    cube('Cyan light strip',(x-w/2+.006,1.707,1.40),(.009,.008,2.54),led,.001)
cx=-.15
for i in range(33):
    x=cx-.76+i*.0475; h=1.17+.14*sin(i*1.7)+.08*cos(i*.63); z=1.86+.05*sin(i*1.12)
    cyl('Bamboo cane %02d'%i,(x,1.682,z),.0205,h,bamboomats[i%5],verts=16)
    for zz in [z-h/2+.17+j*.22 for j in range(7) if z-h/2+.17+j*.22<z+h/2-.02]:
        cyl('Bamboo joint',(x,1.682,zz),.0218,.013,bamboomats[(i+1)%5],verts=16)
fontpath='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
font=bpy.data.fonts.load(fontpath) if os.path.exists(fontpath) else None
for body,z,size in [('WEER',1.95,.40),('S T U D I O',1.68,.115)]:
    halo=text('Illuminated outline '+body,body,(cx,1.625,z),size,warmled,extrude=.006)
    face=text('Dark letter face '+body,body,(cx,1.604,z),size,black if body=='WEER' else white,extrude=.005)
    if font: halo.data.font=font; face.data.font=font
    halo.data.offset=.004

group('90 Lighting and cameras')
world=bpy.data.worlds.new('V02 blue grey studio'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.61,.70,.78,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35; scene.world=world
area('Large softbox',(1,-3,6),450,(.89,.95,1),5,(0,0,.7))
area('Daylight through window',(-1.57,.8,2.0),160,(.85,.93,1),1.5,(.8,-.6,.4))
area('Warm front fill',(3,-.5,3.7),130,(1,.84,.68),3,(0,.7,1))
for x in [-.7,-.15,.4]:
    area('Logo amber wallwash',(x,1.56,1.88),4,(1,.55,.20),.35,(x,1.76,1.88))
data=bpy.data.cameras.new('Isometric reference lens'); cam=bpy.data.objects.new('Camera • reference',data); current.objects.link(cam)
cam.location=(6,-8,6); aim(cam,(0,0,1.15)); cam.data.type='ORTHO'; cam.data.ortho_scale=5.65; scene.camera=cam
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=65
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
try: scene.view_settings.look='AgX - Medium High Contrast'
except: pass
scene.render.film_transparent=False
group('99 Presentation')
ground=material('pale blue studio ground',(.60,.69,.76),.85)
cube('Ground',(0,0,-.215),(200,200,.06),ground,0)
print('PHASE 1 COMPLETE',len(scene.objects))

# PHASE 2: furniture
group('04 Desk and storage')
cube('Desk thin rounded top',(.12,1.105,.795),(2.22,.77,.047),white,.015)
for y in [.795,1.40]: cube('Left desk square leg',(-.92,y,.398),(.047,.047,.75),silver,.005)
cube('Desk structural rail',(.12,1.40,.715),(2.13,.035,.065),white,.004)
cube('Right drawer cabinet',(.96,1.13,.387),(.43,.64,.75),white,.01)
for j in range(4):
    z=.13+j*.178
    cube('Drawer front %d'%j,(.96,.794,z),(.416,.03,.167),white,.005)
    tube('Drawer recessed pull',[(.89,.775,z+.065),(.89,.775,z+.057),(1.025,.775,z+.057),(1.025,.775,z+.065)],.0045,black)
cube('PC tower',(-.70,1.18,.28),(.22,.42,.49),ivory,.01)
cube('PC front inset',(-.70,.961,.28),(.19,.012,.46),silver,.003)
cyl('PC power switch',(-.70,.950,.44),.008,.004,black,rotation=(pi/2,0,0),verts=16)
for z in [.12,.14,.16]: cube('PC ventilation',(-.70,.951,z),(.12,.002,.003),black,0)
# Tall shelf faces front; narrow and close to the window corner.
for x in [-1.67,-1.17]: cube('Tall bookcase side',(x,1.46,1.16),(.025,.40,2.30),white,.004)
cube('Tall bookcase back',(-1.42,1.653,1.16),(.51,.016,2.30),ivory,.002)
for z in [.035,.48,.94,1.39,1.84,2.30]: cube('Tall shelf',(-1.42,1.46,z),(.525,.41,.024),white,.004)
for z in [.94,1.39]:
    cube('Shelf light',(-1.42,1.32,z-.017),(.43,.018,.007),warmled,.001)
    area('Shelf warm light',(-1.42,1.38,z-.05),1.6,(1,.72,.39),.28,(-1.42,1.4,z-.35))
boxblue=material('dust blue storage',(.17,.32,.43),.8)
for i,z in enumerate([.18,.63,1.59,2.00]):
    cube('Storage box',(-1.42,1.44,z),(.39,.30,.22),boxblue if i==0 else paper,.008)
    cube('Box label frame',(-1.42,1.282,z+.015),(.082,.008,.037),silver,.002)
    cube('Box label',(-1.42,1.276,z+.015),(.066,.002,.023),paper,0)
    cube('Box lid',(-1.42,1.44,z+.115),(.405,.31,.018),ivory,.002)
for j in range(6):
    x=-1.60+j*.065
    cube('Tall shelf binder',(x,1.45,1.145),(.046,.255,.37),black if j%3 else paper,.003)
    cube('Binder spine label',(x,1.316,1.23),(.027,.003,.074),white,.001)
    cyl('Binder finger hole',(x,1.310,1.04),.008,.003,silver,rotation=(pi/2,0,0),verts=16)
# Low cabinet aligned with the left wall.
for y in [-.72,.04]: cube('Low cabinet side',(-1.48,y,.32),(.42,.025,.60),white,.004)
for z in [.03,.315,.63]: cube('Low cabinet shelf',(-1.48,-.34,z),(.44,.79,.025),white,.004)
cube('Low cabinet back',(-1.69,-.34,.33),(.018,.78,.6),ivory,.001)
cube('Low cabinet divider',(-1.48,-.34,.33),(.42,.024,.60),white,.003)
cube('Low cabinet closed front',(-1.258,-.145,.18),(.025,.35,.265),white,.004)
cube('Low cabinet pull',(-1.242,-.145,.285),(.007,.07,.012),silver,.002)
for j in range(4):
    y=-.65+j*.072
    cube('Low cabinet black binder',(-1.47,y,.325),(.34,.052,.45),black,.003)
    cube('Low binder label',(-1.291,y,.41),(.002,.028,.10),paper,.001)
for z in [.37,.48]:
    cube('Small document box',(-1.46,-.14,z),(.32,.28,.095),paper,.003)
    cube('Box finger pull',(-1.295,-.14,z),(.005,.05,.01),silver,.001)

group('05 Screens and desk objects')
screenbg=material('CAD navy display',(.013,.022,.032),.38,emission=.20)
screenline=material('CAD pale lines',(.27,.43,.51),.5,emission=.5)
sky=material('display daylight sky',(.47,.64,.74),.5,emission=.5)
# Monitors face the room (-Y), with independent local contents.
for j,x in enumerate([-.38,.40]):
    cube('Monitor aluminium foot', (x,1.18,.84),(.28,.19,.014),silver,.008)
    rod('Monitor stem',(x,1.26,.85),(x,1.26,1.12),.018,silver)
    cube('Monitor thin enclosure',(x,1.26,1.205),(.735,.04,.425),black,.009)
    cube('Monitor display',(x,1.236,1.207),(.704,.003,.393),sky if j==0 else screenbg,.002)
    cube('Monitor lower bezel',(x,1.231,1.008),(.69,.005,.011),silver,.001)
    if j==0:
        # Architecture visualization: shaded towers, window grids and landscaping.
        cube('Screen lawn',(x,1.232,1.059),(.70,.003,.085),leafmats[1],0)
        for k in range(5):
            bx=x-.23+k*.085; h=.15+.065*sin(k*.7)
            cube('Screen building facade',(bx,1.228,1.09+h/2),(.075,.003,h),ivory,0)
            for xx in range(4):
                for zz in range(int(h/.023)):
                    cube('Screen building window',(bx-.027+xx*.018,1.225,1.105+zz*.022),(.01,.002,.013),screenline,0)
        for k in range(7):
            uv('Screen tree',(x+.12+k*.03,1.222,1.11+.018*sin(k)),(.022,.002,.055),leafmats[k%4],12,6)
    else:
        for a,b,c,d in [(-.28,-.125,.28,.12),(-.22,-.10,-.02,.09),(.015,-.10,.23,.09),(-.17,-.02,.16,.055)]:
            tube('CAD plan polyline',[(x+a,1.231,1.20+b),(x+c,1.231,1.20+b),(x+c,1.231,1.20+d),(x+a,1.231,1.20+d)],.00085,screenline,True)
        for k in range(7):
            xx=x-.27+k*.09
            tube('CAD grid',[(xx,1.230,1.035),(xx,1.230,1.37)],.00035,screenline)
            tube('CAD dimension tick',[(xx-.004,1.229,1.045),(xx+.004,1.229,1.055)],.0006,screenline)
        for zz in [1.05,1.35]: tube('CAD dimension baseline',[(x-.29,1.229,zz),(x+.29,1.229,zz)],.00055,screenline)
        for k in range(6): cube('CAD menu bar',(x-.28+k*.065,1.229,1.385),(.044,.002,.004),screenline,0)
cube('Keyboard case',(.03,.901,.840),(.45,.15,.014),silver,.006)
for row in range(5):
    for col in range(15):
        cube('Individual keyboard key',(-.177+col*.029,.842+row*.028,.851),(.024,.023,.005),white,.002)
cube('Spacebar',(.00,.841,.856),(.13,.022,.005),white,.002)
uv('Mouse',(.43,.866,.847),(.037,.059,.017),white)
tube('Mouse split',[(.43,.821,.859),(.43,.853,.864)],.0006,silver)
cube('Mouse wheel',(.43,.843,.865),(.003,.013,.003),black,.001)
for x,y,ang in [(-.75,.90,-.18),(.75,.84,.10)]:
    cube('Phone metal edge',(x,y,.836),(.074,.139,.008),silver,.006,rotation=(0,0,ang))
    cube('Phone black glass',(x,y,.841),(.067,.128,.003),black,.005,rotation=(0,0,ang))
# Articulated lamp.
cyl('Lamp circular base',(-.86,1.15,.839),.082,.015,white)
rod('Lamp lower arm',(-.86,1.15,.85),(-.89,1.18,1.13),.009,silver)
rod('Lamp upper arm',(-.89,1.18,1.13),(-.82,1.15,1.36),.009,silver)
for p in [(-.89,1.18,1.13),(-.82,1.15,1.36)]: uv('Lamp hinge',p,(.017,.017,.017),white)
shade=cyl('Lamp tapered shade',(-.79,1.12,1.335),.051,.083,white,r2=.028)
shade.rotation_euler=(.4,-.35,0)
cyl('Lamp warm diffuser',(-.779,1.108,1.296),.040,.005,warmled)
area('Desk task light',(-.78,1.11,1.27),3,(1,.79,.49),.1,(-.7,1.03,.8))
for x,y in [(-.65,1.17),(.88,1.32)]:
    cyl('Pencil pot',(x,y,.878),.032,.115,potmat)
    cyl('Pencil pot opening',(x,y,.937),.027,.002,black)
    for k in range(7):
        a=k*2*pi/7
        rod('Pencil',(x+.017*cos(a),y+.017*sin(a),.90),(x+.023*cos(a),y+.023*sin(a),1.03+random.uniform(-.018,.018)),.0025,bamboomats[k%5])
cube('Desktop radio enclosure',(1.05,1.21,.946),(.28,.13,.19),ivory,.019)
cube('Radio speaker grille',(1.05,1.138,.947),(.236,.006,.137),edge,.012)
for k in range(20): cube('Speaker grille slot',(.945+k*.011,1.133,.947),(.0015,.002,.118),silver,0)
text('Radio wordmark','STEREO',(1.05,1.127,.951),.016,white,extrude=0)
for x in [.99,1.10]: cyl('Radio dial',(x,1.20,1.045),.011,.007,silver)

group('06 Ergonomic chair')
chair_start=set(scene.objects)
cube('Seat cushion',(0,0,.475),(.48,.47,.085),ivory,.045)
cube('Seat fabric inset',(0,.015,.522),(.423,.397,.012),meshmat,.035)
cyl('Chair gas lift',(0,0,.275),.025,.25,silver)
cyl('Chair gas sleeve',(0,0,.195),.040,.11,white)
cube('Underseat mechanism',(0,-.01,.408),(.18,.18,.05),black,.012)
for i in range(5):
    a=i*2*pi/5+.25
    tube('Five star base spoke',[(0,0,.185),(.15*cos(a),.15*sin(a),.145),(.32*cos(a),.32*sin(a),.096)],.024,white)
    for offset in [-.017,.017]:
        cyl('Twin black caster',(.325*cos(a)+offset,.325*sin(a),.062),.039,.026,black,rotation=(0,pi/2,0),verts=24)
# Gently shaped mesh back, open enough to see through.
def backpos(u,v):
    width=.205+.022*sin(pi*v)-.025*v
    return (u*width,-.218-.095*v+.035*(1-u*u)*sin(v*pi),.60+.50*v)
border=[backpos(-1,i/20) for i in range(21)]+[backpos(-1+2*i/20,1) for i in range(1,21)]+[backpos(1,1-i/20) for i in range(1,21)]+[backpos(1-2*i/20,0) for i in range(1,20)]
tube('Curved back perimeter',border,.015,white,True)
for j in range(39):
    u=-.97+1.94*j/38
    tube('Back mesh vertical',[backpos(u,i/16) for i in range(17)],.0009,meshmat)
for j in range(52):
    v=.02+.96*j/51
    tube('Back mesh horizontal',[backpos(-.98+1.96*i/16,v) for i in range(17)],.0009,meshmat)
tube('Back structural spine',[(0,-.19,.43),(0,-.29,.56),(0,-.325,.73),(0,-.35,.99)],.021,white)
for s in [-1,1]:
    tube('Back fork support',[(0,-.31,.66),(s*.14,-.30,.73),(s*.19,-.28,.87)],.015,white)
    tube('Adjustable arm support',[(s*.20,-.09,.44),(s*.29,-.075,.51),(s*.29,-.075,.67)],.018,silver)
    cube('Armrest pad',(s*.29,-.015,.698),(.071,.26,.036),white,.023)
cube('Lumbar pad',(0,-.22,.73),(.34,.055,.085),meshmat,.03)
rod('Headrest post',(0,-.33,1.055),(0,-.355,1.22),.015,silver)
cube('Headrest frame',(0,-.357,1.22),(.31,.060,.135),white,.045)
cube('Headrest mesh',(0,-.392,1.22),(.264,.007,.092),meshmat,.025)
# Place entire chair facing +Y toward the desk, a slight casual rotation.
chair=bpy.data.objects.new('Chair assembly • faces desk',None); current.objects.link(chair)
for o in set(scene.objects)-chair_start-{chair}: o.parent=chair
chair.location=(.05,.32,.02); chair.rotation_euler.z=-.12

group('07 Rugs and lounge')
cube('Large blue woven desk rug',(.14,.47,.028),(1.96,1.74,.014),rug,.008)
tube('Rug stitched perimeter',[(-.826,-.386,.037),(1.106,-.386,.037),(1.106,1.326,.037),(-.826,1.326,.037)],.002,meshmat,True)
jute=material('natural jute rug',(.41,.35,.25),1,noise=.38,scale=150)
cyl('Round lounge woven rug',(.62,-1.16,.028),.47,.012,jute,verts=96)
for rr in [.10+i*.014 for i in range(26)]:
    tube('Jute concentric weave',[(.62+rr*cos(i*2*pi/120),-1.16+rr*sin(i*2*pi/120),.036) for i in range(120)],.0015,paper,True)
# Organic pouf: deformed rings, depressed top, sewn radial panels.
verts=[]; faces=[]; N=72; R=32
def beanpoint(theta,phi):
    rr=.37*sin(phi)*(1+.035*sin(8*theta)*sin(phi)**2)
    z=.25+.235*cos(phi)-.105*math.exp(-(phi/.5)**2)
    rr*=1+.06*sin(3*theta+1)*sin(phi)
    z+=.007*sin(theta*9+phi*4)*sin(phi)**2
    return (.35+rr*cos(theta),-1.24+rr*sin(theta)*.9,z)
for j in range(R+1):
    for i in range(N): verts.append(beanpoint(i*2*pi/N,j*pi/R))
for j in range(R):
    for i in range(N):
        a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
me=bpy.data.meshes.new('sewn soft beanbag');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('Grey beanbag with folds',me);current.objects.link(ob);me.materials.append(cloth)
for p in me.polygons:p.use_smooth=True
for i in range(8): tube('Beanbag panel seam',[beanpoint(i*2*pi/8,j*pi/64) for j in range(3,62)],.0015,meshmat)
cyl('Round side table body',(.83,-1.06,.23),.205,.39,ivory,verts=64)
cyl('Round side table top',(.83,-1.06,.437),.232,.024,white,verts=64)
for i in range(2): cube('Lounge stacked notebook',(.86,-1.055,.455+i*.015),(.18,.13,.013),black if i==0 else paper,.002,rotation=(0,0,-.2))
cyl('Black coffee mug',(.77,-1.04,.502),.040,.092,black)
cyl('Coffee surface',(.77,-1.04,.549),.033,.002,soil)
tube('Coffee mug handle',[(.77+.040+.026*cos(a),-1.04,.505+.030*sin(a)) for a in [i*2*pi/32 for i in range(32)]],.006,black,True)
# Open bin, with inner wall and visible dark bottom.
cyl('Waste bin inner', (1.40,.63,.15),.090,.26,black)
cu=tube('Waste bin rim',[(1.40+.096*cos(i*2*pi/64),.63+.096*sin(i*2*pi/64),.32) for i in range(64)],.004,silver,True)
v=[];f=[]
for z,r in [(.04,.077),(.32,.096)]:
    for i in range(64):v.append((1.40+r*cos(i*2*pi/64),.63+r*sin(i*2*pi/64),z))
for i in range(64):f.append((i,(i+1)%64,(i+1)%64+64,i+64))
me=bpy.data.meshes.new('Bin hollow wall');me.from_pydata(v,[],f);ob=bpy.data.objects.new('Grey open wastebasket',me);current.objects.link(ob);me.materials.append(silver)
for p in me.polygons:p.use_smooth=True
print('PHASE 2 COMPLETE',len(scene.objects))

# PHASE 3: decor and plants
group('08 Wall accessories')
# Pegboard mounted on the left wall; its normal points +X into the room.
cube('Rounded pegboard',(-1.702,-.35,1.40),(.034,.64,1.00),ivory,.025)
for iy in range(10):
    for iz in range(16):
        cyl('Pegboard perforation',(-1.682,-.626+iy*.0615,.955+iz*.059),.006,.0018,black,rotation=(0,pi/2,0),verts=10)
yellow=material('tool safety yellow',(.70,.45,.025),.5)
toolblue=material('tool blue rubber',(.015,.15,.29),.65)
for i in range(7):
    y=-.59+i*.076; z=1.065 if i<4 else 1.27
    rod('Tool shaft',(-1.658,y,z),(-1.658,y,z+.16),.004,silver)
    rod('Tool rubber handle',(-1.658,y,z-.05),(-1.658,y,z+.018),.012,[black,yellow,toolblue][i%3])
    tube('Pegboard hook',[(-1.677,y,z+.10),(-1.643,y,z+.10),(-1.643,y,z+.115)],.003,silver)
for i in range(3):
    y=-.30+i*.068
    for s in [-1,1]:
        rod('Pliers handle',(-1.65,y+s*.008,1.68),(-1.65,y+s*.019,1.80),.007,[yellow,toolblue,black][i])
        rod('Pliers jaws',(-1.65,y+s*.005,1.81),(-1.65,y+s*.014,1.845),.004,silver)
for y in [-.58,-.46]:
    cube('Pegboard tool cup',(-1.634,y,1.005),(.087,.087,.13),black,.007)
# Safety helmet: dome, projecting brim and molded ribs, not a complete sphere.
vs=[]; fs=[]
for j in range(13):
    phi=(pi/2)*j/12
    for i in range(40):
        a=2*pi*i/40;vs.append((-1.66+.135*cos(phi),-.47+.123*sin(phi)*cos(a),1.48+.17*sin(phi)*sin(a)))
for j in range(12):
    for i in range(40):
        k=j*40+i; kk=j*40+(i+1)%40; fs.append((k,kk,kk+40,k+40))
me=bpy.data.meshes.new('helmet molded dome');me.from_pydata(vs,[],fs);me.materials.append(white)
ob=bpy.data.objects.new('White safety hardhat',me);current.objects.link(ob)
for p in me.polygons:p.use_smooth=True
tube('Helmet projecting brim',[(-1.65,-.47+.14*cos(a),1.48+.185*sin(a)) for a in [i*2*pi/64 for i in range(64)]],.012,white,True)
for yy in [-.505,-.435]:
    tube('Helmet molded ridge',[(-1.54+.015*cos(i*pi/20),yy,1.37+i*.009) for i in range(23)],.006,white)

# Architectural framed art drawn as fine geometry on the paper plane.
def building_art(name,center,width,height,wall):
    x,y,z=center
    if wall=='left':
        cube(name+' black frame',(x,y,z),(.025,width,height),black,.004)
        cube(name+' mat',(x+.016,y,z),(.006,width-.045,height-.045),paper,.001)
        point=lambda u,v:(x+.022,y+u,z+v)
    else:
        cube(name+' black frame',(x,y,z),(width,.025,height),black,.004)
        cube(name+' mat',(x,y-.016,z),(width-.045,.006,height-.045),paper,.001)
        point=lambda u,v:(x+u,y-.022,z+v)
    for i in range(4):
        xx=-width*.32+i*width*.14; hh=height*(.24+.12*sin(i*.8)); ww=width*.11
        tube(name+' tower outline',[point(xx,-height*.23),point(xx,hh),point(xx+ww,hh*.93),point(xx+ww,-height*.23)],.00085,edge)
        for k in range(1,6):
            zz=-height*.23+k*(hh+height*.23)/6
            tube(name+' floors',[point(xx,zz),point(xx+ww,zz)],.00055,edge)
        for k in range(1,3):
            tube(name+' facade',[point(xx+ww*k/3,-height*.23),point(xx+ww*k/3,hh*.94)],.0005,edge)
    tube(name+' ground line',[point(-width*.36,-height*.24),point(width*.35,-height*.24)],.001,edge)
building_art('Left architecture sketch',(-1.701,-.35,2.145),.70,.46,'left')
building_art('Right architecture photo',(1.54,1.69,1.05),.34,.50,'back')

group('09 Clock AC and floating shelves')
for z in [1.30,1.72]: cube('White floating shelf',(1.12,1.58,z),(.60,.30,.028),white,.005)
for j in range(4):
    cube('Stacked shelf book',(1.27,1.56,1.75+j*.034),(.24,.19,.030),[black,paper,edge,paper][j],.002)
    cube('Book page edge',(1.27,1.461,1.75+j*.034),(.218,.003,.021),paper,.001)
cyl('Shelf candle',(1.28,1.57,1.386),.027,.13,paper)
cyl('Candle wick',(1.28,1.57,1.454),.002,.007,black,verts=12)
cube('Small award base',(.94,1.57,1.335),(.065,.065,.03),black,.002)
rod('Small award stem',(.94,1.57,1.345),(.94,1.57,1.44),.008,bamboomats[2])
uv('Award ornament',(.94,1.57,1.45),(.018,.018,.028),silver)
# Clock face lies in XZ; hands and twelve minute indices are on its front.
cyl('Clock black rim',(1.13,1.682,2.16),.185,.026,black,rotation=(pi/2,0,0),verts=64)
cyl('Clock ivory dial',(1.13,1.663,2.16),.174,.012,paper,rotation=(pi/2,0,0),verts=64)
for k in range(12):
    a=k*2*pi/12; r0=.145 if k%3==0 else .151
    tube('Clock hour tick',[(1.13+r0*sin(a),1.654,2.16+r0*cos(a)),(1.13+.162*sin(a),1.654,2.16+.162*cos(a))],.0009,black)
for a,length,r in [(-pi/3,.09,.003),(pi/3,.13,.002),(pi*.94,.14,.0008)]:
    rod('Clock hand',(1.13,1.650,2.16),(1.13+length*sin(a),1.650,2.16+length*cos(a)),r,black)
uv('Clock pivot',(1.13,1.646,2.16),(.006,.003,.006),black)
cube('AC indoor unit',(1.52,1.62,2.40),(.45,.20,.29),white,.038)
cube('AC front fascia',(1.52,1.511,2.415),(.417,.010,.219),ivory,.02)
cube('AC lower outlet',(1.52,1.527,2.29),(.355,.034,.035),edge,.006)
for z in [2.287,2.299]: cube('AC louver',(1.52,1.504,z),(.35,.012,.006),white,.001)
cube('AC status indicator',(1.66,1.501,2.347),(.014,.002,.003),led,.001)

group('10 Botanical details')
def leaf(name,start,end,width,mat,lobed=False):
    start,end=Vector(start),Vector(end); axis=end-start
    side=axis.cross(Vector((0,0,1)))
    if side.length<.001:side=Vector((1,0,0))
    side.normalize(); v=[]; f=[]
    for j in range(17):
        t=j/16; center=start+axis*t+Vector((0,0,.09*axis.length*sin(t*pi)))
        w=width*sin(pi*t)**.75
        if lobed:w*=.48+.52*abs(sin(t*pi*5))**.45
        for s in [-1,0,1]:v.append(tuple(center+side*s*w+Vector((0,0,-abs(s)*.025*sin(t*pi)))))
    for j in range(16):
        for k in range(2):a=j*3+k; f.append((a,a+1,a+4,a+3))
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.materials.append(mat)
    ob=bpy.data.objects.new(name,me);current.objects.link(ob)
    for p in me.polygons:p.use_smooth=True
    so=ob.modifiers.new('leaf thickness','SOLIDIFY');so.thickness=.0007
    tube(name+' midrib',[tuple(start+axis*(j/16)+Vector((0,0,.09*axis.length*sin(j*pi/16)+.001))) for j in range(17)],.0012,leafmats[1])
    return ob
def planter(name,x,y,z,r,h,stand=False):
    cyl(name+' ceramic body',(x,y,z+h/2),r*.83,h,potmat,r2=r,verts=48)
    cyl(name+' soil',(x,y,z+h-.008),r*.9,.01,soil)
    tube(name+' rounded rim',[(x+r*cos(a),y+r*sin(a),z+h) for a in [i*2*pi/64 for i in range(64)]],.006,potmat,True)
    for j in range(38):
        a=random.random()*2*pi; rr=r*.84*random.random()**.5
        uv(name+' white pebble',(x+rr*cos(a),y+rr*sin(a),z+h),(.009,.007,.005),ivory,12,6)
    if stand:
        for j in range(3):
            a=j*2*pi/3
            rod(name+' wood stand',(x+r*cos(a),y+r*sin(a),.035),(x+r*.93*cos(a),y+r*.93*sin(a),z+h*.5),.009,bamboomats[j])
    return z+h
def largeplant(name,x,y,z,r,h,lobed=False):
    top=planter(name,x,y,z,r,h,lobed)
    for j in range(11):
        a=j*2*pi/11+.25; spread=.17+.07*(j%3); height=.24+.11*(j%4)
        start=(x+.02*cos(a),y+.02*sin(a),top)
        mid=(x+spread*.35*cos(a),y+spread*.35*sin(a),top+height*.55)
        end=(x+spread*cos(a),y+spread*sin(a),top+height)
        tube(name+' petiole',[start,mid],.005,leafmats[2])
        leaf(name+' shaped leaf',mid,end,.085 if lobed else .066,leafmats[j%4],lobed)
def smallplant(name,x,y,z,r=.065,trailing=0):
    top=planter(name,x,y,z,r,r*1.5)
    for j in range(14):
        a=j*2*pi/7; rr=r*(1+j%3*.25)
        leaf(name+' small leaf',(x,y,top),(x+rr*cos(a),y+rr*sin(a),top+.04+(j%4)*.025),r*.33,leafmats[j%4])
    if trailing:
        for k in range(3):
            points=[]
            for j in range(22):
                t=j/21;points.append((x+(k-1)*r*.55+.035*sin(t*8+k),y-r-.035*sin(t*6),top-t*trailing))
            tube(name+' trailing vine',points,.002,leafmats[2])
            for j in range(2,21):
                px,py,pz=points[j];sgn=(-1)**j
                leaf(name+' vine leaf',(px,py,pz),(px+sgn*.043,py-.025,pz-.045),.022,leafmats[(j+k)%4])
largeplant('Window broadleaf',-1.19,.86,.027,.185,.34)
largeplant('Right monstera',1.47,1.02,.12,.155,.31,True)
smallplant('Tall shelf pothos',-1.46,1.45,2.325,.073,.66)
smallplant('Floating shelf pothos',.95,1.54,1.735,.065,.79)
smallplant('Pegboard pothos',-1.57,-.09,1.72,.061,.53)
smallplant('Cabinet little plant',-1.47,-.02,.65,.06)
# Reed diffuser alongside the tall plant.
cyl('Reed diffuser bottle',(-1.24,1.47,2.403),.037,.15,paper)
for i in range(5):
    rod('Diffuser reed',(-1.24,1.47,2.44),(-1.24+(i-2)*.015,1.47+.013*sin(i),2.73-abs(i-2)*.016),.0015,bamboomats[1])

group('11 Miniature building model')
cube('Architecture model display base',(-1.47,-.46,.657),(.27,.33,.018),ivory,.002)
for j in range(3):
    x=-1.47; y=-.57+j*.10; h=.095+j*.045
    for xx in [x-.085,x+.085]:
        for yy in [y-.04,y+.04]: rod('Miniature structural column',(xx,yy,.67),(xx,yy,.67+h),.0018,silver)
    for z in [.67,.67+h*.5,.67+h]:
        tube('Miniature floor frame',[(x-.085,y-.04,z),(x+.085,y-.04,z),(x+.085,y+.04,z),(x-.085,y+.04,z)],.0018,silver,True)
    rod('Miniature cross brace',(x+.085,y-.04,.67),(x+.085,y+.04,.67+h),.0012,silver)
print('PHASE 3 COMPLETE',len(scene.objects))

# PHASE 4: final presentation
group('99 Presentation')
cam.location=(7,-7,7.5); aim(cam,(0,0,1.17)); cam.data.ortho_scale=5.80
chair.scale=(1.13,1.10,1.02)
# Cyan panels should read as lacquer, rather than striped wood.
bs=blue.node_tree.nodes.get('Principled BSDF')
for socket in [bs.inputs['Base Color'],bs.inputs['Normal']]:
    for lk in list(socket.links):blue.node_tree.links.remove(lk)
bs.inputs['Base Color'].default_value=(.006,.22,.34,1)
# Dimension annotation geometry, on the presentation ground plane.
dim=material('dimension charcoal',(.10,.14,.17),.8)
for axis in [0,1]:
    if axis==0:
        a=(-1.75,-2.02,-.13);b=(1.75,-2.02,-.13);pos=(0,-2.14,-.125);rotation=(0,0,0)
    else:
        a=(2.02,-1.75,-.13);b=(2.02,1.75,-.13);pos=(2.14,0,-.125);rotation=(0,0,pi/2)
    tube('3.5m dimension line',[a,b],.002,dim)
    av,bv=Vector(a),Vector(b);direction=(bv-av).normalized();perp=Vector((-direction.y,direction.x,0))
    for pt,sgn in [(av,1),(bv,-1)]:
        tube('Dimension extension',[tuple(pt+perp*.05),tuple(pt-perp*.05)],.002,dim)
        tube('Dimension arrow',[tuple(pt+direction*.055*sgn+perp*.015),tuple(pt),tuple(pt+direction*.055*sgn-perp*.015)],.002,dim)
    text('Floor dimension label','3.5 m',pos,.105,dim,rot=rotation,extrude=0)
scene.render.resolution_percentage=100
scene.render.filepath=ROOT+'/Office_Studio_v02_preview.png'
scene['build_script']='build_office_v02.py'
scene['notes']='Reference reconstruction. Individual editable geometry, procedural materials, no external texture dependencies.'
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'
            ar.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Office_Studio_v02.blend')
print('PHASE 4 COMPLETE',len(scene.objects))

# PHASE 5: render-reviewed refinements
for o in scene.objects:
    if o.name.startswith('Clock '):o.location.x-=.14
    if o.name.startswith('AC '):o.location.z+=.09
# Clock curves were created in world coordinates, unlike the dial meshes.
# Moving both data types by the same delta keeps the whole clock together.
for m in leafmats:
    bs=m.node_tree.nodes.get('Principled BSDF')
    for lk in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(lk)
    bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=.42
    bs.inputs['Subsurface Weight'].default_value=.025
for o in list(scene.objects):
    if any(o.name.startswith(p) for p in ['Window broadleaf shaped leaf','Window broadleaf petiole','Right monstera shaped leaf','Right monstera petiole']):
        bpy.data.objects.remove(o,do_unlink=True)
group('10 Botanical details')
for j in range(15):
    a=j*2*pi/9+.3; h=.48+.13*(j%3); radius=.24+.055*(j%3)
    start=(-1.19,.86,.37)
    mid=(-1.19+.06*cos(a),.86+.06*sin(a),.37+h*.32)
    end=(-1.19+radius*cos(a),.86+radius*sin(a),.37+h)
    tube('Window plant arched stem',[start,mid],.004,leafmats[2])
    leaf('Window glossy lance leaf',mid,end,.084,leafmats[j%4])
def monstera_leaf(name,start,end,width,mat):
    start,end=Vector(start),Vector(end);axis=end-start;side=axis.cross(Vector((0,0,1))).normalized()
    vs=[];fs=[];NX=28;NY=40
    for j in range(NY+1):
        t=j/NY
        w=width*sin(pi*t)**.65*(.72+.28*abs(sin(t*pi*5)))
        for i in range(NX+1):
            u=-1+2*i/NX
            p=start+axis*t+side*(u*w)+Vector((0,0,.075*sin(pi*t)-.045*u*u*sin(pi*t)))
            vs.append(tuple(p))
    for j in range(NY):
        for i in range(NX):
            u=-1+2*(i+.5)/NX;t=(j+.5)/NY
            hole=any(((abs(u)-.53)/.115)**2+((t-ht)/.047)**2<1 for ht in [.30,.49,.68])
            if not hole:
                k=j*(NX+1)+i;fs.append((k,k+1,k+NX+2,k+NX+1))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mat)
    ob=bpy.data.objects.new(name,me);current.objects.link(ob)
    for p in me.polygons:p.use_smooth=True
    so=ob.modifiers.new('thin leaf lamina','SOLIDIFY');so.thickness=.0006
    tube(name+' center vein',[tuple(start+axis*(j/20)+Vector((0,0,.076*sin(pi*j/20)))) for j in range(21)],.0013,leafmats[1])
for j in range(10):
    a=j*2*pi/7;h=.25+.13*(j%3);r=.19+.03*(j%3)
    start=(1.47,1.02,.43);mid=(1.47+.035*cos(a),1.02+.035*sin(a),.43+h*.50)
    end=(1.47+r*cos(a),1.02+r*sin(a),.43+h)
    tube('Monstera stem',[start,mid],.004,leafmats[2])
    monstera_leaf('Monstera split leaf',mid,end,.12,leafmats[j%4])
# More natural concrete, wood and fabric response at final resolution.
bs=concrete.node_tree.nodes.get('Principled BSDF')
for n in concrete.node_tree.nodes:
    if n.type=='BUMP':n.inputs['Distance'].default_value=.004
    if n.type=='VALTORGB':
        n.color_ramp.elements[0].color=(.235,.25,.265,1);n.color_ramp.elements[1].color=(.39,.40,.41,1)
for m in woodmats:
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Distance'].default_value=.0014;n.inputs['Strength'].default_value=.20
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.32
for o in scene.objects:
    if o.name.startswith('Waste bin inner'):
        o.scale.z=.15; o.location.z=.06
    if o.name.startswith('Grey open wastebasket'):
        o.data.materials.clear();o.data.materials.append(material('grey bin finish',(.24,.28,.30),.52))
    if o.name.startswith('Doormat'):
        o.data.materials.clear();o.data.materials.append(material('dark entrance weave',(.10,.115,.12),1,noise=.45,scale=170))
# Use indirect light and real reflections for the final render.
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU'
except:scene.cycles.device='CPU'
scene.cycles.max_bounces=6
scene.render.resolution_percentage=100
scene.render.filepath=ROOT+'/Office_Studio_v02_preview.png'
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Office_Studio_v02.blend')
print('REFINEMENTS COMPLETE')

# PHASE 6: final reviewed proportions, materials and detail cameras
for o in scene.objects:
    if o.name.startswith(('Tall bookcase','Tall shelf','Storage box','Box label','Box lid','Binder spine','Binder finger','Shelf light','Shelf warm','Reed diffuser','Diffuser reed')):
        o.location.z*=.93; o.scale.z*=.93
for m in leafmats:
    bs=m.node_tree.nodes.get('Principled BSDF'); c=bs.inputs['Base Color'].default_value
    bs.inputs['Base Color'].default_value=(c[0]*.75,c[1]*.75,c[2]*.75,1)
for n in concrete.node_tree.nodes:
    if n.type=='VALTORGB':
        for e in n.color_ramp.elements:
            c=e.color;e.color=(c[0]*.77,c[1]*.77,c[2]*.77,1)
scene.cycles.samples=48
scene.render.resolution_percentage=100
scene.render.filepath=ROOT+'/Office_Studio_v02_preview.png'
group('90 Lighting and cameras')
for name,position,target,scale in [('Camera • desk detail',(4,-4,3.5),(.10,.8,1.0),2.95),('Camera • wall detail',(2,-3,2.8),(-1.43,-.34,1.35),2.50)]:
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);current.objects.link(o)
    o.location=position;aim(o,target);data.type='ORTHO';data.ortho_scale=scale
scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Office_Studio_v02.blend')
print('FINAL SCENE SAVED. Render the main and detail cameras separately.')
