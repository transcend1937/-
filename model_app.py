"""
万象归踪 — 轮对缺陷智能检测 · 双碳减排演示
检测传感器动态扫描，缺陷红光闪烁，碳减排数据看板
"""
from fastapi import FastAPI, Response
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=800)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>万象归踪 · 节能减碳</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f1a;overflow:hidden;height:100vh;font-family:'PingFang SC','Microsoft YaHei',sans-serif}
#canvas-container{width:100%;height:100vh}
#title-bar{
  position:fixed;top:0;left:0;right:0;z-index:10;
  background:linear-gradient(135deg,rgba(15,23,42,0.92),rgba(30,41,59,0.85));
  backdrop-filter:blur(12px);
  border-bottom:1px solid rgba(56,189,248,0.2);
  padding:10px 24px;display:flex;align-items:center;justify-content:space-between;
}
#title-bar .logo{
  font-size:20px;font-weight:700;
  background:linear-gradient(90deg,#38bdf8,#818cf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  letter-spacing:2px;
}
#title-bar .sub{
  font-size:12px;color:#94a3b8;letter-spacing:4px;
}
#status-panel{
  position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:10;
  background:rgba(15,23,42,0.88);backdrop-filter:blur(12px);
  border:1px solid rgba(56,189,248,0.15);border-radius:12px;
  padding:10px 20px;display:flex;gap:24px;align-items:center;
  font-size:13px;
}
.status-item{display:flex;align-items:center;gap:6px;color:#cbd5e1}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.status-dot.green{background:#22c55e;box-shadow:0 0 6px #22c55e}
.status-dot.red{background:#ef4444;box-shadow:0 0 6px #ef4444}
.status-dot.blue{background:#3b82f6;box-shadow:0 0 6px #3b82f6}
#carbon-badge{
  position:fixed;bottom:80px;right:20px;z-index:10;
  background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);
  border-radius:10px;padding:8px 14px;text-align:center;
}
#carbon-badge .num{font-size:18px;font-weight:700;color:#22c55e}
#carbon-badge .label{font-size:10px;color:#86efac}
#loading{
  position:fixed;inset:0;z-index:100;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:#0f0f1a;color:#38bdf8;font-size:14px;gap:16px;
}
#loading .spinner{width:32px;height:32px;border:3px solid rgba(56,189,248,0.1);border-top:3px solid #38bdf8;border-radius:50%;animation:spin 0.8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div id="loading"><div class="spinner"></div><span>万象归踪 · 场景加载中...</span></div>
<div id="title-bar">
  <div class="logo">⚡ 万象归踪</div>
  <div class="sub">轮对踏面缺陷智能检测 · 碳减排运维</div>
</div>
<div id="canvas-container"></div>
<div id="status-panel">
  <div class="status-item"><span class="status-dot blue"></span>激光扫描中</div>
  <div class="status-item"><span class="status-dot green"></span>轮对 #3 正常</div>
  <div class="status-item"><span class="status-dot red"></span>轮对 #2 缺陷</div>
  <div class="status-item" style="color:#94a3b8">检测效率 12.5s/组</div>
</div>
<div id="carbon-badge">
  <div class="num">12.5<span style="font-size:12px;color:#86efac">kg CO₂</span></div>
  <div class="label">单组轮检测减碳</div>
</div>

<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f0f1a);
scene.fog = new THREE.Fog(0x0f0f1a, 12, 22);

const camera = new THREE.PerspectiveCamera(35, container.clientWidth/container.clientHeight, 0.1, 30);
camera.position.set(3.5, 2.8, 5);
camera.lookAt(0, 0, -3);

const renderer = new THREE.WebGLRenderer({antialias:true,alpha:false});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.25, -3);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 2;
controls.maxDistance = 15;
controls.maxPolarAngle = Math.PI / 2.1;
controls.update();

// 光照
const ambient = new THREE.AmbientLight(0x334466, 0.6);
scene.add(ambient);
const mainLight = new THREE.DirectionalLight(0xffeedd, 1.8);
mainLight.position.set(5, 8, 3);
mainLight.castShadow = true;
mainLight.shadow.mapSize.set(1024,1024);
scene.add(mainLight);
const fillLight = new THREE.DirectionalLight(0x4488ff, 0.5);
fillLight.position.set(-3, 2, -4);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0x88ccff, 0.4);
rimLight.position.set(-2, 1, 6);
scene.add(rimLight);

// ===== 参数 =====
const R = 0.48;
const GAUGE = 1.435;
const NUM_WHEELSETS = 6;
const SPACING = 2.0;

// ===== 材质 =====
const wheelMat = new THREE.MeshStandardMaterial({
  color:0x7a8a9a,metalness:0.65,roughness:0.3,
});
const axleMat = new THREE.MeshStandardMaterial({
  color:0x5a6a7a,metalness:0.7,roughness:0.25,
});
const brakeMat = new THREE.MeshStandardMaterial({
  color:0x3a4a5a,metalness:0.8,roughness:0.2,
});
const railMat = new THREE.MeshStandardMaterial({
  color:0x6a7a8a,metalness:0.6,roughness:0.4,
});
const tieMat = new THREE.MeshStandardMaterial({
  color:0x4a3a2a,roughness:0.9,
});
const groundMat = new THREE.MeshStandardMaterial({
  color:0x2a2a3a,roughness:0.95,metalness:0,
});
const defectMat = new THREE.MeshStandardMaterial({
  color:0xef4444,emissive:0xef4444,emissiveIntensity:0.3,
});

// ===== 地面 =====
const ground = new THREE.Mesh(new THREE.PlaneGeometry(16, 20), groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.y = -0.08;
ground.receiveShadow = true;
scene.add(ground);

// ===== 轨道 (钢轨+轨枕) =====
function createTrack(){
  const g = new THREE.Group();
  // 钢轨
  for(let side of[-1,1]){
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.12, 16), railMat);
    rail.position.set(side*GAUGE/2, 0.06, 0);
    rail.castShadow = true;
    g.add(rail);
  }
  // 轨枕
  for(let z=-7.5; z<=7.5; z+=0.35){
    const tie = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.05, 0.18), tieMat);
    tie.position.set(0, -0.02, z);
    tie.receiveShadow = true;
    g.add(tie);
  }
  return g;
}
scene.add(createTrack());

// ===== 轮对 =====
function createWheel(isDefect=false){
  const group = new THREE.Group();
  // 车轮轮廓 (LatheGeometry)
  const pts = [];
  const step = 0.01;
  // 从轮缘外侧到轮毂中心
  const profile = [
    {x:R+0.04, y:R*0.12},      // 轮缘外侧
    {x:R+0.02, y:R*0.16},      // 轮缘顶部
    {x:R-0.01, y:R*0.10},      // 轮缘喉部
    {x:R-0.03, y:R*0.04},      // 踏面起始
    {x:R-0.06, y:R*0.02},      // 踏面1:20锥度
    {x:R-0.10, y:R*0.005},     // 踏面内侧
    {x:R-0.14, y:-0.002},      // 内侧R角
    {x:R-0.18, y:-0.005},      // 辐板外缘
    {x:R*0.35, y:-0.008},      // 辐板中部
    {x:R*0.20, y:-0.005},      // 辐板内缘
    {x:R*0.15, y:0.002},       // 轮毂外缘
    {x:R*0.08, y:0.008},       // 轮毂内侧
    {x:R*0.04, y:0.015},       // 轮毂中心凸起
    {x:0.02, y:0.015},         // 轴孔边缘
  ];
  for(let p of profile) pts.push(new THREE.Vector2(p.x, p.y));
  for(let i=profile.length-2; i>=0; i--){
    const p = profile[i];
    pts.push(new THREE.Vector2(p.x, -p.y));
  }
  const wheel = new THREE.Mesh(new THREE.LatheGeometry(pts, 48), wheelMat);
  wheel.rotation.z = Math.PI/2;
  wheel.castShadow = true;
  group.add(wheel);

  // 缺陷标记 (仅需一处)
  if(isDefect){
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(R*0.02, 0.008, 8, 24),
      new THREE.MeshBasicMaterial({color:0xff0000,transparent:true,opacity:0.5})
    );
    ring.name='glow';
    ring.rotation.y = Math.PI/2;
    ring.position.set(0, -R*0.05, R*0.05);
    group.add(ring);
    // 缺陷标记点
    for(let i=0;i<8;i++){
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.008, 4, 4),
        defectMat
      );
      dot.name='defect';
      const a=i/8*Math.PI*2;
      dot.position.set(
        0, R*0.7+Math.sin(a)*0.03, Math.cos(a)*0.03
      );
      group.add(dot);
    }
  }
  return group;
}

function createWheelset(zPos, isDefect=false){
  const g = new THREE.Group();
  // 左右车轮
  const lw = createWheel(isDefect);
  lw.position.x = -GAUGE/2;
  g.add(lw);
  const rw = createWheel(isDefect);
  rw.position.x = GAUGE/2;
  g.add(rw);
  // 车轴
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.055, GAUGE+0.1, 12), axleMat);
  axle.rotation.z = Math.PI/2;
  axle.name = 'axle';
  g.add(axle);
  // 轴端凸台
  for(let side of[-1,1]){
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.07, 0.04, 12), axleMat);
    cap.rotation.z = Math.PI/2;
    cap.position.x = side*(GAUGE/2+0.06);
    g.add(cap);
  }
  // 制动盘
  for(let side of[-1,1]){
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.015, 16), brakeMat);
    disc.rotation.z = Math.PI/2;
    disc.position.x = side*(GAUGE/2-0.12);
    g.add(disc);
  }
  g.position.z = zPos;
  return g;
}

// 放置轮对 - 第2组有缺陷
for(let i=0; i<NUM_WHEELSETS; i++){
  const z = i*SPACING - (NUM_WHEELSETS-1)*SPACING/2 - 3;
  const ws = createWheelset(z, i===1);
  scene.add(ws);
}

// ===== 轨边检测传感器阵列 =====
const sensorMat = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.7,roughness:0.3});
const sensorHead = new THREE.MeshStandardMaterial({color:0x60a5fa,emissive:0x3b82f6,emissiveIntensity:0.15});

// 两侧传感器 (对齐第2组轮对位置)
const sensorZ = -3 + 1*SPACING;  // 第2组轮对的Z位置
for(let side of[-1,1]){
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.55, 0.05), sensorMat);
  post.position.set(side*(GAUGE/2+0.35), 0.28, sensorZ);
  post.castShadow = true;
  scene.add(post);
  // 传感器头
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.08, 0.08), sensorHead);
  head.position.set(side*(GAUGE/2+0.42), 0.48, sensorZ);
  head.name='sensor';
  scene.add(head);
  // 传感器指示灯
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.015, 6, 6),
    new THREE.MeshBasicMaterial({color:0xef4444,transparent:true,opacity:0.4})
  );
  dot.position.set(side*(GAUGE/2+0.48), 0.48, sensorZ);
  dot.name='sensorDot';
  scene.add(dot);
}

// ===== 激光扫描线 (扫描缺陷区域) =====
const scanMat = new THREE.MeshBasicMaterial({
  color:0x38bdf8,transparent:true,opacity:0.6
});
const scanLine = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.004, 0.004), scanMat);
scanLine.position.set(0, 0.35, sensorZ);
scanLine.name='scanLine';
scene.add(scanLine);

// ===== 车间背景 =====
const pillarMat = new THREE.MeshStandardMaterial({color:0x3a4a5a,metalness:0.4,roughness:0.6});
const beamMat = new THREE.MeshStandardMaterial({color:0x4a5a6a,metalness:0.3,roughness:0.7});
// 两侧立柱
for(let x of[-3.2, 3.2]){
  for(let z of[-6, -2, 2, 6]){
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.15, 1.8, 0.15), pillarMat);
    pillar.position.set(x, 0.9, z);
    scene.add(pillar);
  }
}
// 横梁
for(let z of[-4, 0, 4]){
  const beam = new THREE.Mesh(new THREE.BoxGeometry(6.4, 0.06, 0.12), beamMat);
  beam.position.set(0, 1.75, z);
  scene.add(beam);
}
// 顶棚灯光
const lightBarMat = new THREE.MeshBasicMaterial({color:0xffffee,transparent:true,opacity:0.06});
for(let z=-5; z<=5; z+=1.5){
  const bar = new THREE.Mesh(new THREE.BoxGeometry(4, 0.02, 0.1), lightBarMat);
  bar.position.set(0, 0.92, z);
  scene.add(bar);
}

document.getElementById('loading').classList.add('hidden');

// ===== 动画 =====
function animate(){
  requestAnimationFrame(animate);
  const t = Date.now();
  const cycle = Math.sin(t * 0.001);  // 1秒周期

  // 缺陷红光闪烁
  scene.children.forEach(obj=>{
    if(obj.type==='Group'){
      obj.children.forEach(ch=>{
        if(ch.name==='defect'){
          ch.material.emissiveIntensity = 0.2 + Math.sin(t*0.006)*0.2;
        }
        if(ch.name==='glow'){
          ch.material.opacity = 0.2 + Math.sin(t*0.008)*0.15;
          const s = 1 + Math.sin(t*0.005)*0.15;
          ch.scale.setScalar(s);
        }
      });
    }
    // 传感器闪烁
    if(obj.name==='sensor'){
      obj.material.emissiveIntensity = 0.1 + Math.sin(t*0.004)*0.08;
    }
    if(obj.name==='sensorDot'){
      obj.material.opacity = 0.3 + Math.sin(t*0.005)*0.3;
    }
  });

  // 扫描线左右摆动
  scanLine.position.x = Math.sin(t * 0.0012) * 1.2;
  scanLine.material.opacity = 0.3 + Math.sin(t * 0.002) * 0.3;

  controls.update();
  renderer.render(scene, camera);
}
animate();

// ===== 响应式 =====
window.addEventListener('resize', ()=>{
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
});
</script>
</body>
</html>'''

@app.get("/")
async def get():
    return Response(HTML, media_type="text/html")