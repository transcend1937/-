"""
万像归踪 — 轮对缺陷智能检测 · 双碳减排演示
双视口：主场景全貌 + 轮对检测放大特写
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
<title>万像归踪-节能减碳 · 轮对智能检测</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a14;overflow:hidden;height:100vh;font-family:'PingFang SC','Microsoft YaHei',sans-serif;color:#e2e8f0}
#title-bar{
  position:fixed;top:0;left:0;right:0;z-index:20;height:52px;
  background:linear-gradient(135deg,rgba(10,15,30,0.96),rgba(20,30,50,0.92));
  backdrop-filter:blur(16px);border-bottom:1px solid rgba(56,189,248,0.25);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;box-shadow:0 4px 30px rgba(0,0,0,0.4);
}
#title-bar .logo{font-size:22px;font-weight:900;letter-spacing:2px;
  background:linear-gradient(135deg,#38bdf8,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
#title-bar .eco{font-size:12px;font-weight:600;color:#4ade80;background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);border-radius:16px;padding:3px 12px;animation:pulseGlow 2s infinite}
@keyframes pulseGlow{0%,100%{box-shadow:0 0 5px rgba(34,197,94,0.2)}50%{box-shadow:0 0 15px rgba(34,197,94,0.4)}}

/* 主视口容器 */
#viewports{position:fixed;top:52px;left:0;right:0;bottom:0;display:flex;flex-direction:row}
#main-view{flex:1;position:relative;border-right:1px solid rgba(56,189,248,0.15)}
#zoom-view{width:36%;min-width:320px;position:relative;background:#080812}
#main-canvas,#zoom-canvas{width:100%;height:100%;display:block}

/* 碳减排数据看板 */
#carbon-dashboard{
  position:fixed;bottom:24px;left:24px;z-index:15;
  background:rgba(10,15,30,0.9);backdrop-filter:blur(12px);
  border:1px solid rgba(34,197,94,0.25);border-radius:14px;
  padding:16px 22px;max-width:320px;
}
#carbon-dashboard .title{font-size:13px;font-weight:600;color:#4ade80;margin-bottom:10px;letter-spacing:2px;display:flex;align-items:center;gap:8px}
#carbon-dashboard .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.carbon-item{text-align:center}
.carbon-item .val{font-size:20px;font-weight:800;color:#22c55e;line-height:1.2}
.carbon-item .val.highlight{color:#fbbf24;font-size:26px}
.carbon-item .lbl{font-size:10px;color:#94a3b8;margin-top:2px}
.carbon-item .unit{font-size:12px;color:#6b7280}

/* 轮对检测详情浮窗 */
#detail-overlay{
  position:absolute;bottom:16px;left:16px;right:16px;z-index:10;
  background:rgba(10,15,30,0.88);backdrop-filter:blur(10px);
  border:1px solid rgba(56,189,248,0.2);border-radius:10px;
  padding:12px 16px;
}
#detail-overlay .row{display:flex;justify-content:space-between;align-items:center;font-size:12px;margin:3px 0}
#detail-overlay .label{color:#94a3b8}
#detail-overlay .value{font-weight:600}
#detail-overlay .value.ok{color:#22c55e}
#detail-overlay .value.warn{color:#fbbf24}
#detail-overlay .value.bad{color:#ef4444}

/* 右视口标题水印 */
#zoom-label{
  position:absolute;top:12px;left:12px;z-index:10;
  font-size:11px;color:rgba(148,163,184,0.6);letter-spacing:2px;
  background:rgba(0,0,0,0.5);padding:4px 10px;border-radius:6px;
}

#loading{position:fixed;inset:0;z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0a0a14;color:#94a3b8;font-size:14px;gap:12px;transition:opacity .6s}
#loading.hidden{opacity:0;pointer-events:none}
.spinner{width:32px;height:32px;border:3px solid rgba(56,189,248,0.15);border-top-color:#38bdf8;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div id="loading"><div class="spinner"></div><span>3D场景加载中...</span></div>

<div id="title-bar">
  <div class="logo">🚂 万像归踪 · 节能减碳</div>
  <div class="eco">🌱 双碳减排</div>
</div>

<div id="viewports">
  <div id="main-view">
    <canvas id="main-canvas"></canvas>
    <div id="carbon-dashboard">
      <div class="title">🌿 碳减排效益 · 单组轮对检测</div>
      <div class="grid">
        <div class="carbon-item"><div class="val highlight" id="co2-save">12.5</div><div class="unit">kg CO₂</div><div class="lbl">每轮对检测减碳</div></div>
        <div class="carbon-item"><div class="val" id="annual-save">5,400</div><div class="unit">吨/年</div><div class="lbl">全路网年减排</div></div>
        <div class="carbon-item"><div class="val" id="energy-save">92%</div><div class="unit">能耗降低</div><div class="lbl">对比人工检测</div></div>
        <div class="carbon-item"><div class="val" id="efficiency">3.2s</div><div class="unit">/组轮对</div><div class="lbl">AI检测耗时</div></div>
      </div>
    </div>
  </div>
  <div id="zoom-view">
    <canvas id="zoom-canvas"></canvas>
    <div id="zoom-label">🔍 轮对特写 · 智能检测</div>
    <div id="detail-overlay">
      <div class="row"><span class="label">检测状态</span><span class="value ok" id="dt-status">✅ 检测中</span></div>
      <div class="row"><span class="label">踏面磨损</span><span class="value warn" id="dt-wear">0.12mm</span></div>
      <div class="row"><span class="label">轮缘厚度</span><span class="value ok" id="dt-flange">32.5mm</span></div>
      <div class="row"><span class="label">碳减排量</span><span class="value ok" id="dt-carbon">12.5 kg CO₂</span></div>
      <div class="row"><span class="label">检测时长</span><span class="value" id="dt-time">0.0s</span></div>
    </div>
  </div>
</div>

<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ===== 常量 =====
const R = 0.46;
const GAUGE = 1.4;
const SPACING = 2.0;
const NUM_WHEELSETS = 6;
const WHEEL_INN = 0.65;  // wheel inner face from center (in local coords before rotation)
const DEFECT_INDEX = 1;   // 第2组有缺陷
const sensorZ = -3 + DEFECT_INDEX*SPACING;  // 缺陷轮对Z位置

// ===== 主场景 =====
const mainCanvas = document.getElementById('main-canvas');
const mainView = document.getElementById('main-view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a14);
scene.fog = new THREE.Fog(0x0a0a14, 12, 22);

const camera = new THREE.PerspectiveCamera(32, mainView.clientWidth/mainView.clientHeight, 0.1, 50);
camera.position.set(3.8, 2.5, 5.5);
camera.lookAt(0, 0.5, -3);
const renderer = new THREE.WebGLRenderer({canvas:mainCanvas,antialias:true});
renderer.setSize(mainView.clientWidth, mainView.clientHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.5, -3);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.5;
controls.minDistance = 2;
controls.maxDistance = 15;
controls.maxPolarAngle = Math.PI/2.2;
controls.update();

// ===== 放大场景 =====
const zoomCanvas = document.getElementById('zoom-canvas');
const zoomView = document.getElementById('zoom-view');
const zoomScene = new THREE.Scene();
zoomScene.background = new THREE.Color(0x080812);

const zoomCamera = new THREE.PerspectiveCamera(22, zoomView.clientWidth/zoomView.clientHeight, 0.1, 20);
zoomCamera.position.set(0.8, 0.65, 1.6);
zoomCamera.lookAt(0, 0.5, sensorZ);
const zoomRenderer = new THREE.WebGLRenderer({canvas:zoomCanvas,antialias:true});
zoomRenderer.setSize(zoomView.clientWidth, zoomView.clientHeight);
zoomRenderer.setPixelRatio(Math.min(devicePixelRatio, 2));
zoomRenderer.toneMapping = THREE.ACESFilmicToneMapping;
zoomRenderer.toneMappingExposure = 1.5;

// ===== 灯光 =====
const ambient = new THREE.AmbientLight(0x334466, 0.6);
scene.add(ambient);
const mainLight = new THREE.DirectionalLight(0xffeedd, 2.0);
mainLight.position.set(5, 8, 3);
mainLight.castShadow = true;
mainLight.shadow.mapSize.set(1024, 1024);
scene.add(mainLight);
const fillLight = new THREE.DirectionalLight(0x8888ff, 0.5);
fillLight.position.set(-3, 4, -2);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0x444488, 0.3);
rimLight.position.set(0, 2, 6);
scene.add(rimLight);

// 放大场景灯光
zoomScene.add(new THREE.AmbientLight(0x446688, 0.5));
const zl = new THREE.DirectionalLight(0xffffff, 2.5);
zl.position.set(2, 3, 4);
zoomScene.add(zl);
const zl2 = new THREE.DirectionalLight(0x4488ff, 0.6);
zl2.position.set(-2, 1, -1);
zoomScene.add(zl2);

// ===== 材质 =====
const wheelMat = new THREE.MeshStandardMaterial({color:0x8a9aaa,metalness:0.7,roughness:0.35});
const rimMat = new THREE.MeshStandardMaterial({color:0x7a8a9a,metalness:0.8,roughness:0.3});
const hubMat = new THREE.MeshStandardMaterial({color:0x9aaaba,metalness:0.6,roughness:0.4});
const axleMat = new THREE.MeshStandardMaterial({color:0x6a7a8a,metalness:0.75,roughness:0.3});
const brakeMat = new THREE.MeshStandardMaterial({color:0x4a5a6a,metalness:0.5,roughness:0.6});
const defectMat = new THREE.MeshStandardMaterial({color:0xff2222,emissive:0xff0000,emissiveIntensity:0.4});
const railMat = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.6,roughness:0.5});
const tieMat = new THREE.MeshStandardMaterial({color:0x3a2a1a,roughness:0.9});
const groundMat = new THREE.MeshStandardMaterial({color:0x2a2a3a,roughness:0.95});

// ===== 地面 =====
const ground = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.set(0, -0.01, 0);
ground.receiveShadow = true;
scene.add(ground);

// ===== 轨道 =====
for(let z=-7; z<=5; z+=0.3){
  const tie = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.04, 0.12), tieMat);
  tie.position.set(0, -0.02, z);
  scene.add(tie);
}
for(let side of[-1,1]){
  const rail = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 14), railMat);
  rail.position.set(side*GAUGE/2, 0.04, -5);
  scene.add(rail);
}

// ===== 轮对创建 =====
function createWheel(isDefect){
  const g = new THREE.Group();

  // 轮缘 (外侧粗环) - 使用TorusGeometry
  const rim = new THREE.Mesh(new THREE.TorusGeometry(R, 0.055, 12, 32), rimMat);
  rim.rotation.z = Math.PI/2;
  g.add(rim);

  // 辐板 (薄连接盘，从内径到轮缘)
  const webOuter = 0.90;  // outer radius of web 
  const webInner = 0.18;  // inner radius (hub edge)
  const webGeom = new THREE.CylinderGeometry(R*webInner, R*webOuter, 0.012, 24, 1, true);
  // We need to fill the open cylinder with caps... simpler: use RingGeometry
  const web = new THREE.Mesh(
    new THREE.RingGeometry(R*webInner, R*webOuter, 24),
    wheelMat
  );
  web.rotation.z = Math.PI/2;
  web.position.x = 0.006;  // slight offset to center of rim
  g.add(web);

  // Second web for the back face
  const web2 = new THREE.Mesh(
    new THREE.RingGeometry(R*webInner, R*webOuter, 24),
    wheelMat
  );
  web2.rotation.z = Math.PI/2;
  web2.position.x = -0.006;
  g.add(web2);

  // Web edge cylinder (connecting front and back rings)
  const webEdge = new THREE.Mesh(
    new THREE.CylinderGeometry(R*webOuter, R*webOuter, 0.012, 24),
    wheelMat
  );
  webEdge.rotation.z = Math.PI/2;
  webEdge.position.x = 0;
  g.add(webEdge);

  // 辐板减重孔 (装饰性凹陷环纹)
  for(let i=0; i<8; i++){
    const angle = (i/8)*Math.PI*2;
    const hole = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.035, 0.014, 6),
      new THREE.MeshStandardMaterial({color:0x2a3a4a,roughness:0.9})
    );
    hole.rotation.z = Math.PI/2;
    const hr = R * 0.55;
    hole.position.set(0, Math.cos(angle)*hr, Math.sin(angle)*hr);
    g.add(hole);
  }

  // 轮毂 (中心凸台)
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.08, 0.05, 20), hubMat);
  hub.rotation.z = Math.PI/2;
  hub.position.x = 0;
  g.add(hub);

  // 轴孔 (中心小洞)
  const hole = new THREE.Mesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.055, 8),
    new THREE.MeshStandardMaterial({color:0x1a1a2a,roughness:1})
  );
  hole.rotation.z = Math.PI/2;
  g.add(hole);

  // 缺陷标记 (仅在指定轮对)
  if(isDefect){
    const glowRing = new THREE.Mesh(
      new THREE.RingGeometry(R*0.75, R*0.85, 24),
      new THREE.MeshBasicMaterial({color:0xff0000,transparent:true,opacity:0.3,side:THREE.DoubleSide})
    );
    glowRing.rotation.z = Math.PI/2;
    glowRing.position.x = 0;
    glowRing.name='glow';
    g.add(glowRing);

    const glowRing2 = new THREE.Mesh(
      new THREE.RingGeometry(R*0.75, R*0.85, 24),
      new THREE.MeshBasicMaterial({color:0xff0000,transparent:true,opacity:0.3,side:THREE.DoubleSide})
    );
    glowRing2.rotation.z = Math.PI/2;
    glowRing2.position.x = -0.012;
    glowRing2.name='glowBack';
    g.add(glowRing2);

    // 缺陷标记点
    for(let j=0; j<5; j++){
      const a = j*1.26 + 0.3;
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.025, 6, 6),
        new THREE.MeshBasicMaterial({color:0xff0000})
      );
      dot.position.set(0, Math.cos(a)*R*0.72, Math.sin(a)*R*0.72);
      dot.name='defect';
      g.add(dot);
    }
  }

  // 制动盘 (车轮内侧)
  for(let side of[-1,1]){
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.015, 16), brakeMat);
    disc.rotation.z = Math.PI/2;
    disc.position.x = side*0.032;
    g.add(disc);
  }

  return g;
}

function createWheelset(zPos, isDefect=false){
  const g = new THREE.Group();
  const lw = createWheel(isDefect);
  lw.position.x = -WHEEL_INN;
  g.add(lw);
  const rw = createWheel(isDefect);
  rw.position.x = WHEEL_INN;
  g.add(rw);

  // 车轴
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, GAUGE+0.2, 12), axleMat);
  axle.rotation.z = Math.PI/2;
  axle.name='axle';
  g.add(axle);

  // 轴端凸台
  for(let side of[-1,1]){
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.058, 0.064, 0.035, 12), axleMat);
    cap.rotation.z = Math.PI/2;
    cap.position.x = side*(GAUGE/2+0.08);
    g.add(cap);
  }

  g.position.z = zPos;
  g.position.y = R + 0.08;
  return g;
}

// ===== 放置轮对 =====
for(let i=0; i<NUM_WHEELSETS; i++){
  const z = i*SPACING - (NUM_WHEELSETS-1)*SPACING/2 - 3;
  const ws = createWheelset(z, i===DEFECT_INDEX);
  scene.add(ws);

  // 放大场景只有检测的轮对
  if(i===DEFECT_INDEX){
    // Clone the wheelset for zoom scene
    const zoomWS = createWheelset(0, true);
    zoomScene.add(zoomWS);
  }
}

// ===== 轨边检测传感器 =====
const sensorMat = new THREE.MeshStandardMaterial({color:0x5a6a7a,metalness:0.7,roughness:0.3});
const sensorHeadMat = new THREE.MeshStandardMaterial({color:0x60a5fa,emissive:0x3b82f6,emissiveIntensity:0.15});
for(let side of[-1,1]){
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.7, 0.05), sensorMat);
  post.position.set(side*(GAUGE/2+0.4), 0.35, sensorZ);
  post.castShadow = true;
  scene.add(post);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.07, 0.07), sensorHeadMat);
  head.position.set(side*(GAUGE/2+0.48), R+0.08, sensorZ);
  head.name='sensor';
  scene.add(head);
  head.castShadow = true;
  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.018, 6, 6),
    new THREE.MeshBasicMaterial({color:0xef4444,transparent:true,opacity:0.4})
  );
  dot.position.set(side*(GAUGE/2+0.54), R+0.08, sensorZ);
  dot.name='sensorDot';
  scene.add(dot);

  // 放大场景也加传感器
  const zpost = post.clone();
  zpost.position.x = side*(GAUGE/2+0.5);
  zoomScene.add(zpost);
  const zhead = head.clone();
  zhead.position.x = side*(GAUGE/2+0.58);
  zhead.name='zsensor';
  zoomScene.add(zhead);
}

// ===== 激光扫描线 =====
const scanMat = new THREE.MeshBasicMaterial({color:0x38bdf8,transparent:true,opacity:0.5});
const scanLine = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.003, 0.003), scanMat);
scanLine.position.set(0, 0.35, sensorZ);
scanLine.name='scanLine';
scene.add(scanLine);

// ===== 车间背景 =====
const pillarMat = new THREE.MeshStandardMaterial({color:0x3a4a5a,metalness:0.4,roughness:0.6});
const beamMat = new THREE.MeshStandardMaterial({color:0x4a5a6a,metalness:0.3,roughness:0.7});
for(let x of[-3.5, 3.5]){
  for(let z of[-7, -3, 1, 5]){
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.15, 1.8, 0.15), pillarMat);
    pillar.position.set(x, 0.9, z);
    scene.add(pillar);
  }
}
for(let z of[-5, -1, 3]){
  const beam = new THREE.Mesh(new THREE.BoxGeometry(7.0, 0.06, 0.12), beamMat);
  beam.position.set(0, 1.75, z);
  scene.add(beam);
}

document.getElementById('loading').classList.add('hidden');

// ===== 动画 =====
function animate(){
  requestAnimationFrame(animate);
  const t = Date.now();
  const delta = 0.016;

  // 缺陷红光闪烁
  scene.children.forEach(obj=>{
    if(obj.type==='Group'){
      obj.children.forEach(ch=>{
        if(ch.name==='defect'){
          ch.material.emissiveIntensity = 0.2 + Math.sin(t*0.006)*0.2;
        }
        if(ch.name==='glow'||ch.name==='glowBack'){
          ch.material.opacity = 0.15 + Math.sin(t*0.008)*0.15;
          const s = 1 + Math.sin(t*0.005)*0.12;
          ch.scale.setScalar(s);
        }
      });
    }
    if(obj.name==='sensor'||obj.name==='zsensor'){
      obj.material.emissiveIntensity = 0.1 + Math.sin(t*0.004)*0.08;
    }
    if(obj.name==='sensorDot'){
      obj.material.opacity = 0.3 + Math.sin(t*0.005)*0.3;
    }
  });

  // 扫描线
  scanLine.position.x = Math.sin(t*0.0012) * 1.2;
  scanLine.material.opacity = 0.3 + Math.sin(t*0.002)*0.3;

  // 更新碳减排数据动画
  const co2Base = 12.5;
  const variation = Math.sin(t*0.0005)*0.3;
  document.getElementById('co2-save').textContent = (co2Base + variation).toFixed(1);
  document.getElementById('dt-carbon').textContent = (co2Base + variation).toFixed(1) + ' kg CO₂';
  document.getElementById('dt-time').textContent = (2.8 + Math.sin(t*0.0008)*0.4).toFixed(1) + 's';

  // 检测状态轮换
  const statusCycle = Math.floor(t/3000) % 3;
  const statusEl = document.getElementById('dt-status');
  if(statusCycle===0){statusEl.textContent='✅ 检测中';statusEl.className='value ok'}
  else if(statusCycle===1){statusEl.textContent='✅ 分析完成';statusEl.className='value ok'}
  else{statusEl.textContent='⚠️ 发现磨损';statusEl.className='value warn'}

  controls.update();
  renderer.render(scene, camera);

  // 放大场景 - 轮对缓慢自转
  zoomScene.children.forEach(obj=>{
    if(obj.type==='Group' && obj.position.z===0){
      obj.children.forEach(w=>{
        if(w.type==='Group'){
          w.children.forEach(m=>{
            if(m.type==='Mesh' && m.name!=='defect' && m.name!=='glow' && m.name!=='glowBack'){
              // non-defect meshes rotate slowly
            }
          });
        }
      });
    }
  });

  // Rotate the axle and wheels in zoom scene
  zoomScene.children.forEach(obj=>{
    if(obj.type==='Group' && obj.position.z===0){
      obj.rotation.x += delta * 0.15;
    }
  });

  zoomRenderer.render(zoomScene, zoomCamera);
}
animate();

// ===== 响应式 =====
function resize(){
  const mw = mainView.clientWidth;
  const mh = mainView.clientHeight;
  camera.aspect = mw/mh;
  camera.updateProjectionMatrix();
  renderer.setSize(mw, mh);

  const zw = zoomView.clientWidth;
  const zh = zoomView.clientHeight;
  zoomCamera.aspect = zw/zh;
  zoomCamera.updateProjectionMatrix();
  zoomRenderer.setSize(zw, zh);
}
window.addEventListener('resize', resize);
// Initial resize to set sizes correctly
setTimeout(resize, 100);
</script>
</body>
</html>'''

@app.get("/")
async def get():
    return Response(HTML, media_type="text/html")