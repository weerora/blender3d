import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { objects, type ObjectId, type Mode, type View } from './catalog';

const baseUrl = import.meta.env.BASE_URL;
export class StudioRoom {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(36, 1, .05, 60);
  readonly renderer: THREE.WebGLRenderer;
  readonly controls: OrbitControls;
  readonly groups = new Map<string, THREE.Object3D>();
  readonly state = { door: false, drawers: [false, false, false, false], drawer: 3, chair: 0, blinds: false, lamp: true, logo: true, monitors: 0, ac: false, temperature: 22 };
  mode: Mode = 'day';
  ready = false;
  selected: ObjectId | null = null;
  touring = false;
  showLabels = true;
  onSelect: (id: ObjectId | null) => void = () => {};
  onHover: (id: ObjectId | null, x: number, y: number) => void = () => {};
  onState: () => void = () => {};
  onCamera: () => void = () => {};
  private model?: THREE.Group;
  private composer: EffectComposer;
  private outline: OutlinePass;
  private ambient = new THREE.HemisphereLight(0xdce8ee, 0xb7a18b, 2.0);
  private sun = new THREE.DirectionalLight(0xfff1d5, 3.2);
  private lampLight = new THREE.PointLight(0xffbd6b, 2, 1.6, 2);
  private logoLight = new THREE.PointLight(0xffc074, 2.2, 2, 2);
  private accentLight = new THREE.PointLight(0x56cfea, 1.1, 2.5, 2);
  private groundMaterial = new THREE.MeshStandardMaterial({ color: 0xeeeae3, roughness: 1 });
  private overlays: THREE.Mesh[] = [];
  private air = new THREE.Group();
  private raycaster = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private pointerStart = { x: 0, y: 0, time: 0 };
  private pointerMoved = false;
  private raf = 0;
  private previousTime = 0;
  private cameraTween?: { start: THREE.Vector3; end: THREE.Vector3; fromTarget: THREE.Vector3; toTarget: THREE.Vector3; startTime: number };
  private resizeObserver: ResizeObserver;
  private originalPositions = new Map<string, THREE.Vector3>();
  private hotspots: { id: ObjectId; el: HTMLButtonElement; point: THREE.Vector3 }[] = [];
  private disposed = false;
  private reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  private envTarget: THREE.WebGLRenderTarget;

  constructor(private container: HTMLElement, hotspotLayer: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.setClearColor(0xeeeae3);
    this.renderer.domElement.setAttribute('aria-label', 'ห้องทำงาน 3 มิติ ลากเพื่อหมุน ใช้แผงวัตถุด้านข้างเพื่อโต้ตอบด้วยแป้นพิมพ์');
    this.renderer.domElement.setAttribute('role', 'img');
    this.container.prepend(this.renderer.domElement);
    this.camera.position.set(6.4, 5.4, 6.4);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 1.15, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = .07;
    this.controls.minDistance = 3.2;
    this.controls.maxDistance = 12;
    this.controls.minPolarAngle = .18;
    this.controls.maxPolarAngle = Math.PI / 2 - .07;
    this.controls.maxTargetRadius = 2;
    this.controls.zoomSpeed = .8;
    this.controls.addEventListener('start', () => { this.cameraTween = undefined; this.touring = false; this.onCamera(); });
    const environment = new RoomEnvironment();
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.envTarget = pmrem.fromScene(environment, .08);
    this.scene.environment = this.envTarget.texture;
    this.scene.environmentIntensity = .35;
    environment.dispose(); pmrem.dispose();
    this.sun.position.set(-2, 6, 4);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    Object.assign(this.sun.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: .1, far: 16 });
    this.sun.shadow.normalBias = .018;
    this.sun.shadow.radius = 3;
    this.sun.shadow.bias = -.0001;
    this.lampLight.position.set(-.78, 1.28, -1.10);
    this.logoLight.position.set(-.15, 1.92, -1.36);
    this.accentLight.position.set(1.10, 1.4, -1.45);
    this.scene.add(this.ambient, this.sun, this.lampLight, this.logoLight, this.accentLight);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), this.groundMaterial);
    ground.rotation.x = -Math.PI / 2; ground.position.y = -.20; ground.receiveShadow = true;
    this.scene.add(ground);
    const renderTarget = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: 4 });
    this.composer = new EffectComposer(this.renderer, renderTarget);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.outline = new OutlinePass(new THREE.Vector2(1, 1), this.scene, this.camera);
    this.outline.edgeStrength = 2.4; this.outline.edgeThickness = 1;
    this.outline.visibleEdgeColor.set('#b58345'); this.outline.hiddenEdgeColor.set('#b58345');
    this.outline.pulsePeriod = 0;
    this.composer.addPass(this.outline);
    this.composer.addPass(new OutputPass());
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.bindPointer();
    for (const id of ['chair', 'monitors', 'lamp', 'door', 'logo', 'ac'] as ObjectId[]) {
      const item = objects.find(o => o.id === id)!;
      const el = document.createElement('button');
      el.className = 'hotspot'; el.setAttribute('aria-label', `เลือก${item.title}`);
      el.dataset.hotspot = id;
      el.innerHTML = '<span></span>';
      el.addEventListener('click', () => this.select(id));
      hotspotLayer.append(el);
      this.hotspots.push({ id, el, point: new THREE.Vector3(...item.focus) });
    }
    this.renderer.domElement.addEventListener('webglcontextlost', this.contextLost);
    this.resize();
    this.raf = requestAnimationFrame(this.frame);
  }
  private contextLost = (event: Event) => {
    event.preventDefault(); this.ready = false;
    this.container.dispatchEvent(new CustomEvent('studio-error', { detail: 'การแสดงผล 3D ถูกพักโดยเบราว์เซอร์ กรุณาโหลดหน้าใหม่', bubbles: true }));
  };
  async load(onProgress: (progress: number) => void) {
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(`${baseUrl}models/office-studio.glb`, event => {
      onProgress(event.total ? Math.min(.9, event.loaded / event.total * .9) : .3);
    });
    if (this.disposed) return;
    this.model = gltf.scene;
    this.model.traverse(o => {
      if (o.userData.interaction) {
        this.groups.set(o.userData.interaction, o);
        this.originalPositions.set(o.userData.interaction, o.position.clone());
      }
      if (o instanceof THREE.Mesh) {
        o.castShadow = true; o.receiveShadow = true;
        // Each primitive owns its runtime material so switches never affect other objects.
        o.material = Array.isArray(o.material) ? o.material.map(m => m.clone()) : o.material.clone();
        const materials = Array.isArray(o.material) ? o.material : [o.material];
        for (const material of materials) {
          const m = material as THREE.MeshStandardMaterial;
          m.envMapIntensity = .35;
          if (m.name.includes('warm halo')) m.emissiveIntensity = 1.8;
          if (m.name.includes('cyan LED')) m.emissiveIntensity = 2.4;
          if (m.name.includes('out of focus')) { m.color.set('#bbcab3'); m.emissive.set('#8e9c82'); m.emissiveIntensity = .2; }
          if (m.name.includes('foliage')) { m.side = THREE.DoubleSide; m.roughness = .62; }
        }
      }
    });
    for (const required of ['chair', 'door', 'monitors', 'lamp', 'blinds', 'logo', 'ac', 'radio', 'drawer_3']) {
      if (!this.groups.has(required)) throw new Error(`Missing model group: ${required}`);
    }
    this.scene.add(this.model);
    this.addFunctionalGeometry(); this.addScreenOverlays(); this.addAir();
    this.ready = true; onProgress(1);
    this.setView('overview', true);
  }
  private addFunctionalGeometry() {
    const findMaterial = (fragment: string) => {
      let found: THREE.Material | undefined;
      this.model!.traverse(o => { if (o instanceof THREE.Mesh) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (!found && m.name.includes(fragment)) found = m; });
      return found ?? new THREE.MeshStandardMaterial({ color: '#d5d5cc' });
    };
    const wood = new THREE.MeshStandardMaterial({ color: '#c8b18c', roughness: .85 });
    const enamel = findMaterial('warm white enamel');
    const concrete = findMaterial('cast concrete');
    const addBox = (parent: THREE.Object3D, name: string, position: number[], size: number[], material: THREE.Material) => {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
      mesh.name = name; mesh.position.fromArray(position); mesh.castShadow = mesh.receiveShadow = true; parent.add(mesh); return mesh;
    };
    const room = this.groups.get('room')!;
    // True doorway in the left wall. Blender (x,y,z) becomes Three.js (x,z,-y).
    addBox(room, 'Door front pier', [-1.8, 1.36, 1.7125], [.12, 2.72, .075], concrete);
    addBox(room, 'Pegboard wall', [-1.8, 1.36, .3475], [.12, 2.72, .915], concrete);
    addBox(room, 'Door lintel', [-1.8, 2.42, 1.24], [.12, .6, .87], concrete);
    const furniture = this.groups.get('furniture')!;
    for (const x of [.752, 1.168]) addBox(furniture, 'Cabinet side', [x, .387, -1.13], [.016, .75, .64], enamel);
    for (const y of [.023, .751]) addBox(furniture, 'Cabinet top or bottom', [.96, y, -1.13], [.43, .022, .64], enamel);
    addBox(furniture, 'Cabinet back', [.96, .387, -1.441], [.43, .75, .018], enamel);
    for (let j = 0; j < 4; j++) {
      const drawer = this.groups.get(`drawer_${j}`)!;
      const y = .13 + j * .178;
      addBox(drawer, 'Drawer wooden base', [.96, y - .070, -1.047], [.375, .012, .47], wood);
      for (const x of [.778, 1.142]) addBox(drawer, 'Drawer wooden side', [x, y - .013, -1.047], [.012, .125, .47], wood);
      addBox(drawer, 'Drawer wooden back', [.96, y - .013, -1.276], [.375, .125, .012], wood);
    }
  }
  private addScreenOverlays() {
    for (const x of [-.38, .40]) {
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(.705, .393), new THREE.MeshBasicMaterial({ color: '#0e1b23', toneMapped: false }));
      mesh.position.set(x, 1.207, -1.219);
      mesh.visible = false; mesh.userData.interaction = 'monitors';
      this.scene.add(mesh); this.overlays.push(mesh);
    }
  }
  private addAir() {
    for (let j = 0; j < 3; j++) {
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(1.4 + j * .1, 2.36, -1.49),
        new THREE.Vector3(1.4 + j * .1, 2.22, -1.37),
        new THREE.Vector3(1.38 + j * .1, 2.08, -1.26),
      ]);
      this.air.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 16, .005, 4, false), new THREE.MeshBasicMaterial({ color: '#9bd8e3', transparent: true, opacity: .6 })));
    }
    this.air.visible = false; this.scene.add(this.air);
  }
  private bindPointer() {
    const el = this.renderer.domElement;
    el.addEventListener('pointerdown', event => { this.pointerStart = { x: event.clientX, y: event.clientY, time: performance.now() }; this.pointerMoved = false; });
    el.addEventListener('pointermove', event => {
      if (Math.hypot(event.clientX - this.pointerStart.x, event.clientY - this.pointerStart.y) > 5) this.pointerMoved = true;
      if (event.buttons || !this.ready) { this.onHover(null, 0, 0); return; }
      const id = this.pick(event.clientX, event.clientY);
      el.style.cursor = id ? 'pointer' : 'grab'; this.onHover(id, event.clientX, event.clientY);
    });
    el.addEventListener('pointerleave', () => this.onHover(null, 0, 0));
    el.addEventListener('pointerup', event => {
      if (this.pointerMoved || performance.now() - this.pointerStart.time > 500 || event.button !== 0 || !this.ready) return;
      this.select(this.pick(event.clientX, event.clientY));
    });
    el.addEventListener('dblclick', event => { const id = this.pick(event.clientX, event.clientY); if (id) this.focus(id); });
  }
  private pick(x: number, y: number): ObjectId | null {
    if (!this.model) return null;
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.set((x - rect.left) / rect.width * 2 - 1, -(y - rect.top) / rect.height * 2 + 1);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects([this.model, ...this.overlays.filter(o => o.visible)], true);
    if (!hits.length) return null;
    let o: THREE.Object3D | null = hits[0].object;
    while (o) {
      const key: string | undefined = o.userData.interaction;
      if (key?.startsWith('drawer_')) { this.state.drawer = Number(key.split('_')[1]); return 'drawers'; }
      if (objects.some(item => item.id === key)) return key as ObjectId;
      o = o.parent;
    }
    return null;
  }
  select(id: ObjectId | null) {
    if (!this.ready) return;
    this.selected = id;
    const key = id === 'drawers' ? `drawer_${this.state.drawer}` : id;
    this.outline.selectedObjects = key && this.groups.has(key) ? [this.groups.get(key)!] : [];
    this.hotspots.forEach(h => h.el.classList.toggle('selected', h.id === id));
    this.onSelect(id);
  }
  setDrawer(index: number) { this.state.drawer = THREE.MathUtils.clamp(index, 0, 3); this.select('drawers'); }
  activate(id: ObjectId) {
    if (!this.ready) return;
    switch (id) {
      case 'chair': this.state.chair += Math.PI / 2; break;
      case 'door': this.state.door = !this.state.door; break;
      case 'drawers': this.state.drawers[this.state.drawer] = !this.state.drawers[this.state.drawer]; break;
      case 'blinds': this.state.blinds = !this.state.blinds; break;
      case 'lamp': this.state.lamp = !this.state.lamp; this.setEmission('lamp', this.state.lamp); break;
      case 'logo': this.state.logo = !this.state.logo; this.setEmission('logo', this.state.logo); break;
      case 'ac': this.state.ac = !this.state.ac; this.air.visible = this.state.ac; break;
      case 'monitors': this.state.monitors = (this.state.monitors + 1) % 3; this.updateScreens(); break;
    }
    this.onState();
  }
  private setEmission(id: string, on: boolean) {
    this.groups.get(id)?.traverse(o => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of (Array.isArray(o.material) ? o.material : [o.material]) as THREE.MeshStandardMaterial[]) {
        if (m.name.includes('warm halo')) m.emissiveIntensity = on ? 1.8 : 0;
      }
    });
  }
  private updateScreens() {
    this.overlays.forEach((mesh, i) => {
      mesh.visible = this.state.monitors !== 0;
      const material = mesh.material as THREE.MeshBasicMaterial;
      material.map?.dispose(); material.map = null;
      if (this.state.monitors === 1) {
        const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 360;
        const ctx = canvas.getContext('2d')!;
        ctx.fillStyle = i ? '#e9e2d4' : '#203f36'; ctx.fillRect(0, 0, 640, 360);
        ctx.fillStyle = i ? '#203f36' : '#ebe8da';
        ctx.font = '18px sans-serif'; ctx.fillText(i ? 'A LITTLE SPACE TO THINK.' : 'WEER / FOCUS MODE', 40, 48);
        ctx.font = i ? '60px Georgia' : '80px Georgia';
        ctx.fillText(i ? 'Make something' : 'One thing', 40, 180);
        ctx.fillText(i ? 'meaningful.' : 'at a time.', 40, 255);
        ctx.font = '15px sans-serif'; ctx.fillText(i ? 'DESIGN. BUILD. REPEAT.' : 'LESS NOISE. MORE IDEAS.', 40, 325);
        const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace;
        material.map = texture; material.color.set('white');
      } else material.color.set('#091013');
      material.needsUpdate = true;
    });
  }
  setMode(mode: Mode) {
    this.mode = mode;
    document.documentElement.dataset.mode = mode;
    this.renderer.setClearColor(mode === 'night' ? 0x283332 : 0xeeeae3);
    this.groundMaterial.color.set(mode === 'night' ? 0x283332 : 0xeeeae3);
    this.scene.environmentIntensity = mode === 'night' ? .1 : .35;
    this.onState();
  }
  setView(view: View, instant = false) {
    const views = {
      overview: { position: [6.7, 5.65, 6.7], target: [0, .94, 0] },
      desk: { position: [3.5, 2.9, 3.3], target: [.1, 1.03, -.75] },
      lounge: { position: [3.5, 3.5, 5.5], target: [.35, .48, .45] },
    };
    const { position, target } = views[view]; this.touring = false;
    const destination = new THREE.Vector3(...position);
    const center = new THREE.Vector3(...target);
    if (view === 'overview' && this.camera.aspect < .98) destination.sub(center).multiplyScalar(.98 / this.camera.aspect).add(center);
    this.fly(destination, center, instant);
    this.onCamera();
  }
  focus(id: ObjectId) {
    const item = objects.find(o => o.id === id)!;
    const target = new THREE.Vector3(...item.focus);
    this.fly(target.clone().add(new THREE.Vector3(2.9, 1.9, 3.0)), target);
  }
  private fly(end: THREE.Vector3, toTarget: THREE.Vector3, instant = false) {
    if (instant || this.reducedMotion) { this.camera.position.copy(end); this.controls.target.copy(toTarget); this.controls.update(); return; }
    this.cameraTween = { start: this.camera.position.clone(), end, fromTarget: this.controls.target.clone(), toTarget, startTime: performance.now() };
  }
  toggleTour() { this.touring = !this.touring; this.cameraTween = undefined; this.onCamera(); }
  setQuality(high: boolean) {
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, high ? 1.75 : 1));
    this.composer.setPixelRatio(this.renderer.getPixelRatio());
    this.resize();
  }
  setShadows(value: boolean) { this.renderer.shadowMap.enabled = value; this.renderer.shadowMap.needsUpdate = true; }
  setExposure(value: number) { this.renderer.toneMappingExposure = value; }
  project(id: ObjectId) {
    const item = objects.find(o => o.id === id)!;
    const p = new THREE.Vector3(...item.focus).project(this.camera);
    const rect = this.renderer.domElement.getBoundingClientRect();
    return { x: rect.left + (p.x + 1) / 2 * rect.width, y: rect.top + (1 - p.y) / 2 * rect.height };
  }
  private resize() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    if (!w || !h) return;
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h); this.composer.setSize(w, h);
  }
  private frame = (time: number) => {
    if (this.disposed) return;
    this.raf = requestAnimationFrame(this.frame);
    const delta = Math.min((time - this.previousTime) / 1000, .05); this.previousTime = time;
    if (document.hidden) return;
    const speed = this.reducedMotion ? 100 : 7;
    const damp = (a: number, b: number) => THREE.MathUtils.damp(a, b, speed, delta);
    const door = this.groups.get('door'); if (door) door.rotation.y = damp(door.rotation.y, this.state.door ? -Math.PI * .44 : 0);
    const chair = this.groups.get('chair'); if (chair) chair.rotation.y = damp(chair.rotation.y, this.state.chair);
    const blinds = this.groups.get('blinds'); if (blinds) blinds.scale.y = damp(blinds.scale.y, this.state.blinds ? .09 : 1);
    this.state.drawers.forEach((open, index) => {
      const object = this.groups.get(`drawer_${index}`); const origin = this.originalPositions.get(`drawer_${index}`);
      if (object && origin) object.position.z = damp(object.position.z, origin.z + (open ? .28 : 0));
    });
    this.ambient.intensity = damp(this.ambient.intensity, this.mode === 'night' ? .48 : 2.0);
    this.sun.intensity = damp(this.sun.intensity, this.mode === 'night' ? .30 : 3.2);
    this.lampLight.intensity = damp(this.lampLight.intensity, this.state.lamp ? (this.mode === 'night' ? 3 : 1.5) : 0);
    this.logoLight.intensity = damp(this.logoLight.intensity, this.state.logo ? (this.mode === 'night' ? 3.0 : 1.8) : 0);
    this.accentLight.intensity = damp(this.accentLight.intensity, this.mode === 'night' ? 2.4 : .6);
    if (this.air.visible) this.air.children.forEach((o, i) => { (o as THREE.Mesh).position.y = this.reducedMotion ? 0 : -.03 * (1 + Math.sin(time * .003 + i)); });
    if (this.cameraTween) {
      const t = Math.min((time - this.cameraTween.startTime) / 850, 1); const ease = t * t * (3 - 2 * t);
      this.camera.position.lerpVectors(this.cameraTween.start, this.cameraTween.end, ease);
      this.controls.target.lerpVectors(this.cameraTween.fromTarget, this.cameraTween.toTarget, ease);
      if (t === 1) this.cameraTween = undefined;
    } else if (this.touring && !this.reducedMotion) {
      const angle = .78 + Math.sin(time * .00012) * .48;
      this.camera.position.set(Math.sin(angle) * 8.5, 5.1, Math.cos(angle) * 8.5);
      this.controls.target.set(0, 1.1, 0);
    }
    this.controls.update();
    const w = this.container.clientWidth, h = this.container.clientHeight;
    this.hotspots.forEach(hotspot => {
      const p = hotspot.point.clone().project(this.camera);
      const visible = this.ready && this.showLabels && !this.touring && p.z < 1 && Math.abs(p.x) < .98 && Math.abs(p.y) < .93;
      hotspot.el.hidden = !visible;
      if (visible) hotspot.el.style.transform = `translate(${(p.x + 1) * w / 2}px, ${(1 - p.y) * h / 2}px) translate(-50%, -50%)`;
    });
    if (this.outline.selectedObjects.length) this.composer.render(); else this.renderer.render(this.scene, this.camera);
  };
  getStats() { return { ready: this.ready, triangles: this.renderer.info.render.triangles, calls: this.renderer.info.render.calls, groups: this.groups.size, mode: this.mode, selected: this.selected, state: this.state }; }
  dispose() {
    this.disposed = true; cancelAnimationFrame(this.raf); this.resizeObserver.disconnect(); this.controls.dispose();
    this.scene.traverse(o => { if (o instanceof THREE.Mesh) { o.geometry.dispose(); (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => { (m as THREE.MeshStandardMaterial).map?.dispose(); m.dispose(); }); } });
    this.envTarget.dispose(); this.composer.dispose(); this.renderer.dispose();
  }
}
