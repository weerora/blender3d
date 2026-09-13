"""Run through Blender MCP. Evaluates a COPY of v02 into compact interaction groups."""
import bpy, os, json, math
from mathutils import Vector, Matrix
ROOT='/Users/alphaone/Blender3D-MCP'
source=next((s for s in bpy.data.scenes if s.name.startswith('WEER Studio')),None)
if source is None: raise RuntimeError('Open Office_Studio_v02.blend first.')
bpy.context.window.scene=source
depsgraph=bpy.context.evaluated_depsgraph_get()
os.makedirs(ROOT+'/assets-source',exist_ok=True)
os.makedirs(ROOT+'/public/models',exist_ok=True)

def classify(o):
    n=o.name
    col=' '.join(c.name for c in o.users_collection)
    if n.startswith(('Ground','Floor dimension','3.5m dimension','Dimension ')):return None
    # Replace render-only solid blocks with real doorway/cabinet openings in the runtime.
    if n in {'Right drawer cabinet','Left wall door and pegboard section'}:return None
    if '06 Ergonomic chair' in col:return 'chair'
    if n.startswith(('Door slab','Door recessed','Door handle','Door lever')):return 'door'
    if n.startswith('Drawer front'):
        return 'drawer_'+n.split('Drawer front ')[1].split('.')[0]
    if n.startswith('Drawer recessed pull'):
        suffix=n.split('.')[-1] if '.' in n else '0'
        return 'drawer_'+str(int(suffix))
    if n.startswith(('Venetian blind','Blind tape')):return 'blinds'
    if n.startswith(('Monitor','Screen ','CAD ')):return 'monitors'
    if n.startswith('Lamp '):return 'lamp'
    if n.startswith(('Illuminated outline','Dark letter face')):return 'logo'
    if n.startswith(('AC ',)):return 'ac'
    if n.startswith(('Clock ',)):return 'clock'
    if n.startswith(('Desktop radio','Radio ','Speaker grille')):return 'radio'
    if '10 Botanical' in col:return 'plants'
    if '07 Rugs' in col:
        if n.startswith(('Grey beanbag','Beanbag','Round side','Lounge stacked','Black coffee','Coffee ','Round lounge','Jute ')):return 'lounge'
        return 'decor'
    if '08 Wall accessories' in col or '11 Miniature' in col:return 'pegboard'
    if '04 Desk' in col:return 'furniture'
    if '05 Screens' in col:return 'desktop'
    if '09 Clock' in col:return 'shelves'
    return 'room'

pivots={'chair':(.05,.32,.02),'door':(-1.70,-1.675,0),'blinds':(-1.68,.815,2.48)}
buffers={}; originals=0
for o in list(source.objects):
    if o.type not in {'MESH','CURVE','FONT','SURFACE'}:continue
    key=classify(o)
    if not key:continue
    ev=o.evaluated_get(depsgraph)
    me=ev.to_mesh()
    if not me:continue
    if not me.vertices:ev.to_mesh_clear();continue
    data=buffers.setdefault(key,{'vertices':[],'faces':[],'material_ids':[],'materials':[]})
    offset=len(data['vertices']);origin=Vector(pivots.get(key,(0,0,0)))
    transform=o.matrix_world
    data['vertices'].extend(tuple(transform@v.co-origin) for v in me.vertices)
    matmap=[]
    for mat in me.materials:
        if mat not in data['materials']:data['materials'].append(mat)
        matmap.append(data['materials'].index(mat))
    if not matmap:
        if None not in data['materials']:data['materials'].append(None)
        matmap=[data['materials'].index(None)]
    for p in me.polygons:
        data['faces'].append(tuple(offset+i for i in p.vertices))
        data['material_ids'].append(matmap[min(p.material_index,len(matmap)-1)])
    ev.to_mesh_clear();originals+=1

webscene=bpy.data.scenes.new('WEB_EXPORT_TEMP')
bpy.context.window.scene=webscene
matcache={}
def webmat(src):
    key=src.name if src else 'default'
    if key in matcache:return matcache[key]
    m=bpy.data.materials.new('WEB_'+key);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    color=src.diffuse_color[:] if src else (.6,.6,.6,1)
    if src and src.use_nodes:
        old=src.node_tree.nodes.get('Principled BSDF')
        if old:
            if not old.inputs['Base Color'].is_linked:color=old.inputs['Base Color'].default_value[:]
            for channel in ['Roughness','Metallic','Emission Color','Emission Strength']:
                if channel in old.inputs:bs.inputs[channel].default_value=old.inputs[channel].default_value
    bs.inputs['Base Color'].default_value=color;m.diffuse_color=color
    matcache[key]=m;return m
try:
    report={'source':source.name,'sourceObjects':originals,'groups':[]}
    for key,data in buffers.items():
        me=bpy.data.meshes.new('WEB_'+key)
        me.from_pydata(data['vertices'],[],data['faces']);me.update()
        for m in data['materials']:me.materials.append(webmat(m))
        for p,idx in zip(me.polygons,data['material_ids']):p.material_index=idx
        # Quantization may re-center mesh nodes. An empty parent preserves the authored pivot.
        root=bpy.data.objects.new(key,None);webscene.collection.objects.link(root)
        root.location=pivots.get(key,(0,0,0));root['interaction']=key
        o=bpy.data.objects.new(key+'_geometry',me);webscene.collection.objects.link(o)
        o.parent=root;o.location=(0,0,0)
        report['groups'].append({'id':key,'vertices':len(me.vertices),'polygons':len(me.polygons)})
    path=ROOT+'/assets-source/office-studio.glb'
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_apply=False,export_yup=True)
    report['bytes']=os.path.getsize(path)
    with open(ROOT+'/assets-source/export-report.json','w') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
finally:
    bpy.context.window.scene=source
    for o in list(webscene.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.scenes.remove(webscene)
