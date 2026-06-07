"""
万象归踪 — 3D轮对排列展示
仅轮对平行排列在轨道上，中间车轴相连，无检测元素
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>轮对排列</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;overflow:hidden;height:100vh}
#c{width:100%;height:100vh}
#loading{position:fixed;inset:0;background:#1a1a2e;display:flex;align-items:center;justify-content:center;z-index:999;color:rgba(255,255,255,.4);font-size:14px;font-family:sans-serif;transition:opacity .5s}
#loading.hidden{opacity:0;pointer-events:none}
.hint{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);color:rgba(255,255,255,.25);font-size:12px;font-family:sans-serif;z-index:10;letter-spacing:1px}
</style>
</head>
<body>
<div id="c"></div>
<div id="loading">加载中...</div>
<div class="hint">拖拽旋转 · 滚轮缩放</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

<script>
const c = document.getElementById('c');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const camera = new THREE.PerspectiveCamera(30, c.clientWidth/c.clientHeight, 0.1, 50);
camera.position.set(5, 3, 7);
camera.lookAt(0, 0.3, 0);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(c.clientWidth, c.clientHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
c.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.target.set(0, 0.3, 0);
controls.maxPolarAngle = Math.PI / 2.2;
controls.minDistance = 3;
controls.maxDistance = 20;

// Lights
scene.add(new THREE.AmbientLight(0x222244, 0.6));
scene.add(new THREE.HemisphereLight(0x60a5fa, 0x1a1a2e, 0.6));
const dirLight = new THREE.DirectionalLight(0xffeedd, 1.2);
dirLight.position.set(6, 12, 4);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);
const fill = new THREE.DirectionalLight(0x60a5fa, 0.3);
fill.position.set(-4, 2, -6);
scene.add(fill);

// Ground
const g = new THREE.Mesh(
  new THREE.PlaneGeometry(20, 28),
  new THREE.MeshStandardMaterial({color:0x2a2a3e,roughness:0.9,metalness:0.05})
);
g.rotation.x = -Math.PI/2;
g.position.y = -0.1;
g.receiveShadow = true;
scene.add(g);

// Track rails
const railMat = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.8,roughness:0.3});
for(let side of[-1,1]){
  const rail = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 16), railMat);
  rail.position.set(side*0.72, 0.06, 0);
  rail.castShadow = true;
  scene.add(rail);
}
// Sleepers
const sleeperMat = new THREE.MeshStandardMaterial({color:0x6a5a4a,roughness:0.9});
for(let z=-7; z<=7; z+=0.7){
  const s = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.05, 0.1), sleeperMat);
  s.position.set(0, -0.06, z);
  scene.add(s);
}

// Wheel profile - LatheGeometry
const R = 0.48, T = 0.10;
const pts = [
  [R+0.04, T/2+0.02], [R+0.02, T/2], [R, T/2-0.01],
  [R-0.005, T/2-0.02], [R-0.015, 0],
  [R-0.005, -T/2+0.02], [R, -T/2+0.01],
  [R+0.02, -T/2], [R+0.04, -T/2-0.02],
];
const profile = pts.map(p=>new THREE.Vector2(p[0], p[1]));

const webPts = [
  [0.20, T/2-0.01], [R-0.03, T/2-0.02],
  [R-0.03, -T/2+0.02], [0.20, -T/2+0.01],
];
const webProfile = webPts.map(p=>new THREE.Vector2(p[0], p[1]));

const wheelMat = new THREE.MeshStandardMaterial({color:0x7a8b9a,metalness:0.7,roughness:0.3});
const rimMat = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.8,roughness:0.25});
const axleMat = new THREE.MeshStandardMaterial({color:0x3a4a5a,metalness:0.85,roughness:0.2});
const hubMat = new THREE.MeshStandardMaterial({color:0x6a7a8a,metalness:0.6,roughness:0.35});

const AXLE_LEN = 1.44;

function makeWheel(hasDefect){
  const g = new THREE.Group();
  // 车轮主体 - LatheGeometry绕Y轴
  const wheel = new THREE.Mesh(new THREE.LatheGeometry(profile, 36), wheelMat);
  wheel.castShadow = true;
  g.add(wheel);
  // 轮辐
  const web = new THREE.Mesh(new THREE.LatheGeometry(webProfile, 24), wheelMat);
  g.add(web);
  // 轮毂
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.17, 0.06, 12), hubMat);
  g.add(hub);
  // 整体绕Z转90°，车轮轴从Y变成X，轮面朝Z（平行轨道）
  g.rotation.z = Math.PI/2;

  // 缺陷标记
  if(hasDefect){
    const defMat = new THREE.MeshStandardMaterial({
      color:0xf87171,emissive:0xf87171,emissiveIntensity:0.5
    });
    const def = new THREE.Mesh(new THREE.SphereGeometry(0.04,8,8), defMat);
    def.position.set(R-0.01, 0, 0.08);
    def.name='defect';
    g.add(def);
    // 光晕环
    const glowRing = new THREE.Mesh(
      new THREE.RingGeometry(0.06,0.1,16),
      new THREE.MeshBasicMaterial({color:0xf87171,transparent:true,opacity:0.3})
    );
    glowRing.position.set(R-0.01, 0, 0.085);
    glowRing.rotation.x = -Math.PI/2;
    glowRing.name='glow';
    g.add(glowRing);
  }
  return g;
}

// 6组轮对
for(let i=0; i<6; i++){
  const grp = new THREE.Group();
  const z = (i-2.5)*2.2;

  // 左右车轮
  const isDefect = (i===1); // 第2组有缺陷
  for(let side of[-1,1]){
    const w = makeWheel(isDefect);
    w.position.x = side*AXLE_LEN/2;
    grp.add(w);
  }

  // 车轴（柱子）
  const axle = new THREE.Mesh(
    new THREE.CylinderGeometry(0.07, 0.07, AXLE_LEN, 12),
    axleMat
  );
  axle.rotation.z = Math.PI/2;
  grp.add(axle);

  // 轴端凸台
  for(let side of[-1,1]){
    const cap = new THREE.Mesh(
      new THREE.CylinderGeometry(0.13, 0.15, 0.05, 12),
      hubMat
    );
    cap.rotation.z = Math.PI/2;
    cap.position.x = side*(AXLE_LEN/2+0.025);
    grp.add(cap);
  }

  // 制动盘
  for(let side of[-1,1]){
    const disc = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.02, 24),
      new THREE.MeshStandardMaterial({color:0x555566,metalness:0.5,roughness:0.6})
    );
    disc.rotation.z = Math.PI/2;
    disc.position.x = side*(AXLE_LEN/2-0.08);
    grp.add(disc);
  }

  grp.position.set(0, R+0.06, z);
  scene.add(grp);
}

// 车间背景柱
const pillarMat = new THREE.MeshStandardMaterial({color:0x3a4a5a,metalness:0.6,roughness:0.5});
for(let side of[-1,1])
  for(let z=-5; z<=5; z+=2.5){
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 0.1), pillarMat);
    p.position.set(side*2.2, 0.4, z);
    scene.add(p);
  }

// 横梁
const beamMat = new THREE.MeshStandardMaterial({color:0x4a5a6a,metalness:0.5,roughness:0.6});
for(let z=-5; z<=5; z+=2.5){
  const b = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.06, 0.08), beamMat);
  b.position.set(0, 0.85, z);
  scene.add(b);
}

// 顶灯光条
const lightMat = new THREE.MeshBasicMaterial({color:0xffffee,transparent:true,opacity:0.08});
for(let z=-4; z<=4; z+=2){
  const s = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.02, 0.15), lightMat);
  s.position.set(0, 0.9, z);
  scene.add(s);
}

// 轨边检测传感器
const sensorFrame = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.7,roughness:0.3});
const sensorBlue = new THREE.MeshStandardMaterial({color:0x60a5fa,emissive:0x60a5fa,emissiveIntensity:0.1});
// 左侧传感器（位于第2组轮对附近）
for(let side of[-1,1]){
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.06), sensorFrame);
  post.position.set(side*1.1, 0.25, -1.8);
  scene.add(post);
  const sensor = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.08, 0.08), sensorBlue);
  sensor.position.set(side*1.16, 0.45, -1.8);
  sensor.name='sensor';
  scene.add(sensor);
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.02, 6, 6),
    new THREE.MeshBasicMaterial({color:0xef4444})
  );
  dot.position.set(side*1.22, 0.45, -1.8);
  dot.name='sensorDot';
  scene.add(dot);
}

document.getElementById('loading').classList.add('hidden');

function animate(){
  requestAnimationFrame(animate);

  // 缺陷红光闪烁 + 传感器闪烁
  const t = Date.now();
  scene.children.forEach(obj=>{
    if(obj.type==='Group'){
      obj.children.forEach(ch=>{
        if(ch.name==='defect') ch.material.emissiveIntensity = 0.2+Math.sin(t*0.006)*0.2;
        if(ch.name==='glow'){
          ch.material.opacity = 0.2+Math.sin(t*0.008)*0.15;
          ch.scale.setScalar(1+Math.sin(t*0.005)*0.15);
        }
      });
    }
    if(obj.name==='sensor'){
      obj.material.emissiveIntensity = 0.08+Math.sin(t*0.004)*0.06;
    }
    if(obj.name==='sensorDot'){
      obj.material.opacity = 0.3+Math.sin(t*0.005)*0.3;
    }
  });

  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', ()=>{
  camera.aspect = c.clientWidth/c.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(c.clientWidth, c.clientHeight);
});
</script>
</body>
</html>'''

@app.get("/")
@app.get("/model/")
async def index():
    return HTMLResponse(HTML)