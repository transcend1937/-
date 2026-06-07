"""
万象归踪 — 3D交互模型展示网站（高仿真版）
完整火车车辆 + 真实轮对 + 双视角
"""
from fastapi import FastAPI, Response
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>万象归踪 · 3D智能检测模拟</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{overflow:hidden;background:#0a0e1a;font-family:'PingFang SC','Microsoft YaHei',sans-serif;color:#fff}
#canvas-container{width:100vw;height:100vh;display:block}

/* HUD overlay */
#hud{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);display:flex;gap:16px;z-index:100;
  background:rgba(10,14,26,0.75);backdrop-filter:blur(12px);padding:18px 32px;border-radius:16px;
  border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 32px rgba(0,0,0,0.5)}
.hud-item{text-align:center;min-width:80px}
.hud-item .num{font-size:24px;font-weight:700;background:linear-gradient(135deg,#34d399,#06b6d4);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent}
.hud-item .num.gold{background:linear-gradient(135deg,#fbbf24,#f59e0b);-webkit-background-clip:text}
.hud-item .num.rose{background:linear-gradient(135deg,#fb7185,#ec4899);-webkit-background-clip:text}
.hud-item .num.blue{background:linear-gradient(135deg,#60a5fa,#3b82f6);-webkit-background-clip:text}
.hud-item .label{font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px;letter-spacing:1px}
.hud-divider{width:1px;background:rgba(255,255,255,0.1);align-self:stretch}

/* Title bar */
#title{position:fixed;top:24px;left:50%;transform:translateX(-50%);z-index:100;
  text-align:center;pointer-events:none}
#title h1{font-size:22px;font-weight:700;background:linear-gradient(135deg,#34d399,#06b6d4,#60a5fa);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;letter-spacing:2px}
#title p{font-size:12px;color:rgba(255,255,255,0.4);margin-top:4px;letter-spacing:4px}

/* Detail panel */
#detail-panel{position:fixed;right:24px;top:50%;transform:translateY(-50%);z-index:100;
  background:rgba(10,14,26,0.7);backdrop-filter:blur(12px);padding:20px;border-radius:14px;
  border:1px solid rgba(255,255,255,0.06);width:180px}
#detail-panel h3{font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:2px;margin-bottom:12px}
.detail-row{display:flex;justify-content:space-between;padding:6px 0;font-size:13px;
  border-bottom:1px solid rgba(255,255,255,0.04)}
.detail-row .v{color:#34d399;font-weight:600}
.detail-row .v.warn{color:#fbbf24}
.detail-row .v.ok{color:#34d399}

/* Zoomed wheel view (bottom-right corner) */
#wheel-zoom{position:fixed;left:24px;bottom:110px;z-index:100;
  width:200px;height:200px;border-radius:14px;overflow:hidden;
  border:1px solid rgba(255,255,255,0.1);background:rgba(10,14,26,0.8);
  box-shadow:0 8px 32px rgba(0,0,0,0.4)}
#wheel-zoom canvas{width:100% !important;height:100% !important}
#wheel-zoom .label{position:absolute;top:8px;left:10px;font-size:9px;color:rgba(255,255,255,0.35);
  letter-spacing:1px;pointer-events:none}

/* Scan indicator */
#scan-status{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:50;
  pointer-events:none;font-size:14px;color:rgba(52,211,153,0.6);letter-spacing:3px;
  opacity:0;transition:opacity 0.3s}
#scan-status.active{opacity:1}

@media(max-width:768px){
  #hud{bottom:12px;padding:12px 16px;gap:8px;flex-wrap:wrap;justify-content:center;border-radius:10px;
    width:calc(100% - 24px)}
  .hud-item{min-width:60px}.hud-item .num{font-size:18px}.hud-item .label{font-size:10px}
  #title h1{font-size:16px}#title p{font-size:10px}
  #detail-panel{display:none}
  #wheel-zoom{left:12px;bottom:80px;width:130px;height:130px}
}
</style>
</head>
<body>
<div id="title"><h1>🚂 万象归踪 · 智能检测降碳</h1><p>SIMULATION · 3D INTERACTIVE</p></div>
<div id="scan-status">⚡ 检测扫描中 ...</div>
<div id="canvas-container"></div>
<div id="wheel-zoom"><div class="label">🔍 轮对剖面</div></div>
<div id="detail-panel">
  <h3>检测数据</h3>
  <div class="detail-row"><span>轮位</span><span class="v" id="d-pos">—</span></div>
  <div class="detail-row"><span>踏面状态</span><span class="v ok" id="d-surface">正常</span></div>
  <div class="detail-row"><span>缺陷等级</span><span class="v" id="d-defect">—</span></div>
  <div class="detail-row"><span>减碳量</span><span class="v" id="d-carbon">—</span></div>
</div>
<div id="hud">
  <div class="hud-item"><div class="num" id="scan-count">0</div><div class="label">检测轮对</div></div>
  <div class="hud-divider"></div>
  <div class="hud-item"><div class="num gold" id="defect-found">0</div><div class="label">缺陷发现</div></div>
  <div class="hud-divider"></div>
  <div class="hud-item"><div class="num rose" id="carbon-total">0.0</div><div class="label">碳减排(kg)</div></div>
  <div class="hud-divider"></div>
  <div class="hud-item"><div class="num blue" id="efficiency">0%</div><div class="label">效率提升</div></div>
</div>

<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ====== Scene Setup ======
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x0a0e1a, 30, 70);

const camera = new THREE.PerspectiveCamera(35, container.clientWidth/container.clientHeight, 0.1, 100);
camera.position.set(14, 8, 18);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.5, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 5;
controls.maxDistance = 35;
controls.maxPolarAngle = Math.PI / 2.1;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.8;
controls.update();

// ====== Lighting ======
const ambient = new THREE.AmbientLight(0x334466, 0.6);
scene.add(ambient);

const dirLight = new THREE.DirectionalLight(0xffeedd, 2.5);
dirLight.position.set(15, 20, 10);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
dirLight.shadow.camera.near = 1;
dirLight.shadow.camera.far = 40;
dirLight.shadow.camera.left = -15;
dirLight.shadow.camera.right = 15;
dirLight.shadow.camera.top = 15;
dirLight.shadow.camera.bottom = -5;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x4488ff, 0.5);
fillLight.position.set(-10, 5, -10);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0x66ccff, 0.8);
rimLight.position.set(0, -5, -15);
scene.add(rimLight);

// Point lights near the inspection area
const scannerLight = new THREE.PointLight(0x00ffaa, 1, 5);
scannerLight.position.set(0, 1.2, 0);
scene.add(scannerLight);

const alertLight = new THREE.PointLight(0xff4444, 0, 4);
alertLight.position.set(0, 2, 0);
scene.add(alertLight);

// ====== Ground ======
const groundGeo = new THREE.PlaneGeometry(60, 60);
const groundMat = new THREE.MeshStandardMaterial({color:0x0d1117, roughness:0.9, metalness:0.1});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.y = -0.45;
ground.receiveShadow = true;
scene.add(ground);

// Grid
const gridHelper = new THREE.GridHelper(30, 30, 0x1a2640, 0x111833);
gridHelper.position.y = -0.4;
scene.add(gridHelper);

// ====== Helper: Create Realistic Train Wheel ======
function createTrainWheel(color=0x555555, detail=false){
  const group = new THREE.Group();
  
  // Wheel profile based on actual railway wheel (using LatheGeometry)
  const pts = [];
  const scale = 0.42; // radius
  
  // Realistic wheel cross-section profile (from flange to tread)
  // Flange (highest point)
  pts.push(new THREE.Vector2(0.90*scale, 0.32*scale));
  pts.push(new THREE.Vector2(0.85*scale, 0.31*scale));
  pts.push(new THREE.Vector2(0.78*scale, 0.28*scale));
  // Flange tip
  pts.push(new THREE.Vector2(0.72*scale, 0.26*scale));
  pts.push(new THREE.Vector2(0.68*scale, 0.24*scale));
  // Flange root / throat
  pts.push(new THREE.Vector2(0.65*scale, 0.18*scale));
  // Tread (running surface)
  pts.push(new THREE.Vector2(0.62*scale, 0.12*scale));
  pts.push(new THREE.Vector2(0.55*scale, 0.06*scale));
  // Tread taper
  pts.push(new THREE.Vector2(0.42*scale, 0.02*scale));
  pts.push(new THREE.Vector2(0.30*scale, 0*scale));
  // Inner rim
  pts.push(new THREE.Vector2(0.15*scale, 0*scale));
  pts.push(new THREE.Vector2(0.08*scale, -0.02*scale));
  // Web plate inner
  pts.push(new THREE.Vector2(0.05*scale, -0.04*scale));
  pts.push(new THREE.Vector2(0.04*scale, -0.15*scale));
  // Hub
  pts.push(new THREE.Vector2(0.04*scale, -0.22*scale));
  pts.push(new THREE.Vector2(0.08*scale, -0.24*scale));
  
  // Mirror to other side for full profile
  const profile = [];
  for(let p of pts) profile.push(new THREE.Vector2(p.x, p.y));
  // Add symmetric bottom
  for(let i=pts.length-2; i>=0; i--){
    const p = pts[i];
    profile.push(new THREE.Vector2(p.x, -p.y));
  }
  
  const wheelMat = new THREE.MeshStandardMaterial({
    color: color, metalness: 0.7, roughness: 0.4,
    side: THREE.DoubleSide
  });
  
  const wheelGeo = new THREE.LatheGeometry(profile, 36);
  const wheel = new THREE.Mesh(wheelGeo, wheelMat);
  wheel.castShadow = true;
  group.add(wheel);
  
  // Axle
  const axleMat = new THREE.MeshStandardMaterial({color:0x333333, metalness:0.8, roughness:0.3});
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.8, 12), axleMat);
  axle.rotation.z = Math.PI/2;
  group.add(axle);
  
  // Brake disc
  const discMat = new THREE.MeshStandardMaterial({color:0x444444, metalness:0.6, roughness:0.5});
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.04, 24), discMat);
  disc.rotation.x = Math.PI/2;
  disc.position.x = 0.5;
  group.add(disc);
  
  const disc2 = disc.clone();
  disc2.position.x = -0.5;
  group.add(disc2);
  
  return group;
}

// ====== Build Wheelset (2 wheels + axle) ======
function createWheelset(xPos=0, color=0x555555){
  const group = new THREE.Group();
  
  // Left wheel
  const leftWheel = createTrainWheel(color);
  leftWheel.position.z = -0.88;
  leftWheel.position.x = 0;
  group.add(leftWheel);
  
  // Right wheel
  const rightWheel = createTrainWheel(color);
  rightWheel.position.z = 0.88;
  rightWheel.position.x = 0;
  group.add(rightWheel);
  
  // Axle (already included in each wheel, but add center axle)
  const axleMat = new THREE.MeshStandardMaterial({color:0x3a3a3a, metalness:0.7, roughness:0.3});
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 1.76, 10), axleMat);
  axle.rotation.z = Math.PI/2;
  group.add(axle);
  
  group.position.x = xPos;
  group.position.y = 0.24;
  return group;
}

// ====== Build Bogle (2 wheelsets + frame) ======
function createBogie(xPos=0, color=0x555555){
  const group = new THREE.Group();
  
  // Frame
  const frameMat = new THREE.MeshStandardMaterial({color:0x2a2a2a, metalness:0.5, roughness:0.6});
  const frame = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.12, 1.4), frameMat);
  frame.position.y = 0.22;
  group.add(frame);
  
  // Cross beams
  for(let z of [-0.45, 0.45]){
    const beam = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.08, 0.12), frameMat);
    beam.position.set(0, 0.22, z);
    group.add(beam);
  }
  
  // Springs
  const springMat = new THREE.MeshStandardMaterial({color:0x444444, metalness:0.3, roughness:0.5});
  for(let z of [-0.45, 0.45]){
    for(let x of [-0.45, 0.45]){
      const spring = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.1, 8), springMat);
      spring.position.set(x, 0.35, z);
      group.add(spring);
    }
  }
  
  // Two wheelsets
  const ws1 = createWheelset(-0.5, color);
  ws1.position.y = -0.05;
  group.add(ws1);
  
  const ws2 = createWheelset(0.5, color);
  ws2.position.y = -0.05;
  group.add(ws2);
  
  group.position.x = xPos;
  group.position.y = 0.15;
  return group;
}

// ====== Build Locomotive Body ======
function createLocomotive(){
  const group = new THREE.Group();
  
  const bodyColor = 0x1a3a6a; // Deep blue like SS series
  const bodyMat = new THREE.MeshStandardMaterial({color: bodyColor, metalness:0.3, roughness:0.4});
  const accentMat = new THREE.MeshStandardMaterial({color: 0xc41e3a, metalness:0.2, roughness:0.5});
  const cabMat = new THREE.MeshStandardMaterial({color: 0x0d1f3c, metalness:0.3, roughness:0.3});
  const glassMat = new THREE.MeshStandardMaterial({
    color: 0x88ccff, metalness:0.9, roughness:0.1, transparent:true, opacity:0.3
  });
  const detailMat = new THREE.MeshStandardMaterial({color: 0xdddddd, metalness:0.5, roughness:0.3});
  
  // Main body
  const mainBody = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.9, 4.0), bodyMat);
  mainBody.position.y = 0.75;
  mainBody.castShadow = true;
  group.add(mainBody);
  
  // Cab (front section, slightly raised)
  const cab = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.65, 0.8), cabMat);
  cab.position.set(0, 1.2, 2.25);
  cab.castShadow = true;
  group.add(cab);
  
  // Cab windshield
  const windshield = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.35, 0.05), glassMat);
  windshield.position.set(0, 1.25, 2.7);
  group.add(windshield);
  
  // Cab windows (sides)
  for(let z of [1.9, 2.4]){
    for(let x of [-0.75, 0.75]){
      const win = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.25, 0.3), glassMat);
      win.position.set(x, 1.2, z);
      group.add(win);
    }
  }
  
  // Side windows
  for(let z of [-1.5, -0.5, 0.5, 1.5]){
    for(let x of [-0.85, 0.85]){
      const win = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.25, 0.5), glassMat);
      win.position.set(x, 0.8, z);
      group.add(win);
    }
  }
  
  // Roof
  const roofMat = new THREE.MeshStandardMaterial({color: 0xeeeeee, metalness:0.1, roughness:0.6});
  const roof = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.08, 3.8), roofMat);
  roof.position.y = 1.2;
  group.add(roof);
  
  // Roof equipment
  for(let z of [-1.2, 0, 1.2]){
    const unit = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.12, 0.5), detailMat);
    unit.position.set(0, 1.3, z);
    group.add(unit);
  }
  
  // Pantograph (simplified)
  const pantoBase = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.08, 0.3), detailMat);
  pantoBase.position.set(0, 1.35, -1.5);
  group.add(pantoBase);
  
  const pantoArm = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.4, 0.04), detailMat);
  pantoArm.position.set(0, 1.6, -1.5);
  group.add(pantoArm);
  
  const pantoHead = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.04, 0.08), detailMat);
  pantoHead.position.set(0, 1.82, -1.5);
  group.add(pantoHead);
  
  // Red accent stripe
  for(let x of [-0.86, 0.86]){
    const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.06, 3.6), accentMat);
    stripe.position.set(x, 0.55, 0);
    group.add(stripe);
  }
  
  // Headlights
  const lightMat = new THREE.MeshStandardMaterial({color:0xffdd44, emissive:0xffaa00, emissiveIntensity:0.5});
  for(let x of [-0.4, 0.4]){
    const hl = new THREE.Mesh(new THREE.CircleGeometry(0.12, 16), lightMat);
    hl.position.set(x, 0.75, 2.05);
    hl.rotation.y = Math.PI/2;
    group.add(hl);
  }
  
  // Couplers
  const couplerMat = new THREE.MeshStandardMaterial({color:0x555555, metalness:0.6, roughness:0.4});
  const coupler = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.12, 0.3), couplerMat);
  coupler.position.set(0, 0.4, 2.05);
  group.add(coupler);
  const coupler2 = coupler.clone();
  coupler2.position.z = -2.05;
  group.add(coupler2);
  
  // Undercarriage details
  const underMat = new THREE.MeshStandardMaterial({color:0x222222, metalness:0.3, roughness:0.6});
  const under = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.15, 3.2), underMat);
  under.position.y = 0.28;
  group.add(under);
  
  return group;
}

// ====== Build Rail Track ======
function createTrack(){
  const group = new THREE.Group();
  
  const railMat = new THREE.MeshStandardMaterial({color:0x777777, metalness:0.8, roughness:0.3});
  const sleeperMat = new THREE.MeshStandardMaterial({color:0x5a3d2b, roughness:0.9});
  const ballastMat = new THREE.MeshStandardMaterial({color:0x3a3028, roughness:1.0});
  
  // Ballast
  const ballast = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.06, 9), ballastMat);
  ballast.position.set(0, -0.42, 0);
  group.add(ballast);
  
  // Sleepers (wooden ties)
  for(let z = -4.2; z <= 4.2; z += 0.35){
    const sleeper = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.05, 0.12), sleeperMat);
    sleeper.position.set(0, -0.36, z);
    group.add(sleeper);
  }
  
  // Rails
  for(let x of [-0.52, 0.52]){
    // Rail base
    const railBase = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.03, 8.5), railMat);
    railBase.position.set(x, -0.32, 0);
    group.add(railBase);
    // Rail head
    const railHead = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.08, 8.5), railMat);
    railHead.position.set(x, -0.26, 0);
    group.add(railHead);
    // Rail web
    const railWeb = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.06, 8.5), railMat);
    railWeb.position.set(x, -0.29, 0);
    group.add(railWeb);
  }
  
  group.position.y = 0;
  return group;
}

// ====== Build Inspection Gantry ======
function createGantry(){
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({color:0x2288cc, metalness:0.5, roughness:0.3});
  const mat2 = new THREE.MeshStandardMaterial({color:0x1166aa, metalness:0.4, roughness:0.4});
  const lightMat = new THREE.MeshStandardMaterial({
    color:0x00ffaa, emissive:0x00ffaa, emissiveIntensity:0.3
  });
  
  // Side pillars
  for(let x of [-1.2, 1.2]){
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 0.1), mat2);
    pillar.position.set(x, 0.4, 0);
    group.add(pillar);
  }
  
  // Top beam
  const beam = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.06, 0.15), mat);
  beam.position.set(0, 0.8, 0);
  group.add(beam);
  
  // Camera units (5 on each side)
  for(let side of [-1, 1]){
    for(let i = -2; i <= 2; i++){
      const cam = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.12, 0.1), mat);
      cam.position.set(side * 0.65, 0.65, i * 0.15);
      // Camera lens
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.03, 8), lightMat);
      lens.position.set(side * 0.68, 0.65, i * 0.15);
      lens.rotation.y = side > 0 ? -Math.PI/2 : Math.PI/2;
      group.add(lens);
      group.add(cam);
    }
  }
  
  // Laser line emitter
  const laserMat = new THREE.MeshStandardMaterial({
    color:0x00ff88, emissive:0x00ff88, emissiveIntensity:0.5, transparent:true, opacity:0.3
  });
  const laserBar = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.01, 0.01), laserMat);
  laserBar.position.set(0, 0.35, 0);
  group.add(laserBar);
  
  // Status indicator
  const statusLight = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 8), new THREE.MeshStandardMaterial({
    color:0x00ff88, emissive:0x00ff88, emissiveIntensity:0.5
  }));
  statusLight.position.set(0, 0.85, 0);
  group.add(statusLight);
  
  return group;
}

// ====== Build Inspection Rail (separate zoom view scene) ======
function buildInspectionRail(scene){
  const mat = new THREE.MeshStandardMaterial({color:0x666666, metalness:0.7, roughness:0.3});
  for(let x of [-0.52, 0.52]){
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.08, 2), mat);
    rail.position.set(x, -0.42, 0);
    scene.add(rail);
  }
}

// ====== Assemble Main Scene ======

// Track
const track = createTrack();
track.position.z = 0;
scene.add(track);

// Locomotive
const loco = createLocomotive();
loco.position.set(0, 0.1, 0);
scene.add(loco);

// Bogies
const bogie1 = createBogie(-0.8);
scene.add(bogie1);
const bogie2 = createBogie(0.8);
scene.add(bogie2);

// Inspection gantry
const gantry = createGantry();
gantry.position.set(3.0, 0, 1.5);
scene.add(gantry);

// Additional track section near gantry for inspection
const track2 = createTrack();
track2.position.set(3.0, 0, 1.5);
scene.add(track2);

// ====== Second Scene: Zoomed Wheel View ======
const zoomContainer = document.getElementById('wheel-zoom');
const zoomScene = new THREE.Scene();
zoomScene.background = new THREE.Color(0x0a0e1a);

const zoomCamera = new THREE.PerspectiveCamera(30, 1, 0.01, 10);
zoomCamera.position.set(0.5, 0.3, 1.2);
zoomCamera.lookAt(0, 0.05, 0);

const zoomRenderer = new THREE.WebGLRenderer({antialias:true});
zoomRenderer.setSize(zoomContainer.clientWidth, zoomContainer.clientHeight);
zoomRenderer.setPixelRatio(Math.min(devicePixelRatio, 2));
zoomRenderer.toneMapping = THREE.ACESFilmicToneMapping;
zoomRenderer.toneMappingExposure = 1.0;
zoomContainer.appendChild(zoomRenderer.domElement);

// Zoom scene lighting
const zAmbient = new THREE.AmbientLight(0x446688, 0.8);
zoomScene.add(zAmbient);
const zDir = new THREE.DirectionalLight(0xffffff, 2);
zDir.position.set(2, 3, 2);
zoomScene.add(zDir);

// Create detailed wheel for zoom view
const zoomWheel = createTrainWheel(0x8899aa, true);
zoomWheel.scale.set(0.8, 0.8, 0.8);
zoomWheel.position.set(0, 0.2, 0);
zoomWheel.rotation.x = Math.PI/2;
zoomScene.add(zoomWheel);

// Rail in zoom view
const zRailMat = new THREE.MeshStandardMaterial({color:0x888888, metalness:0.8, roughness:0.3});
for(let x of [-0.4, 0.4]){
  const rail = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.06, 0.6), zRailMat);
  rail.position.set(x, -0.18, 0);
  zoomScene.add(rail);
}

// Grid in zoom
const zGrid = new THREE.GridHelper(0.8, 8, 0x1a2a44, 0x0f1a33);
zGrid.position.y = -0.2;
zoomScene.add(zGrid);

// ====== Scan Animation Variables ======
let scanPos = -1.5;
let scanDir = 1;
let isDefect = false;
let scanCount = 0;
let defectCount = 0;
let carbonTotal = 0;
let wheelAngle = 0;
let scanActive = false;

// Defect markers (random positions on wheels)
const defects = [];
for(let i = 0; i < 3; i++){
  defects.push({
    axle: Math.floor(Math.random() * 4),
    angle: Math.random() * Math.PI * 2,
    severity: 0.3 + Math.random() * 0.5
  });
}
let currentDefect = null;

// ====== Scan Line ======
const scanLineMat = new THREE.MeshBasicMaterial({
  color: 0x00ff88, transparent: true, opacity: 0.4
});
const scanLine = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.005, 0.005), scanLineMat);
scanLine.position.set(0, 0.35, scanPos);
scene.add(scanLine);

// Scan laser sheet
const sheetMat = new THREE.MeshBasicMaterial({
  color: 0x00ff88, transparent: true, opacity: 0.08, side: THREE.DoubleSide
});
const sheet = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 1.0), sheetMat);
sheet.rotation.x = Math.PI/2;
sheet.position.set(0, 0.35, scanPos);
scene.add(sheet);

// Defect markers on wheels (small red spheres)
const defectMarkers = [];
for(let i = 0; i < 4; i++){ // 4 wheelsets
  for(let side of [-1, 1]){
    const dm = new THREE.Mesh(
      new THREE.SphereGeometry(0.02, 8, 8),
      new THREE.MeshStandardMaterial({color:0xff4444, emissive:0xff2222, emissiveIntensity:0.3})
    );
    dm.visible = false;
    dm.position.set(side * 0.05, 0.3, -0.45 + i * 0.3);
    scene.add(dm);
    defectMarkers.push(dm);
  }
}

// ====== UI Elements ======
const scanCountEl = document.getElementById('scan-count');
const defectFoundEl = document.getElementById('defect-found');
const carbonTotalEl = document.getElementById('carbon-total');
const efficiencyEl = document.getElementById('efficiency');
const scanStatus = document.getElementById('scan-status');
const dPos = document.getElementById('d-pos');
const dSurface = document.getElementById('d-surface');
const dDefect = document.getElementById('d-defect');
const dCarbon = document.getElementById('d-carbon');

// ====== Animation Loop ======
const clock = new THREE.Clock();

function animate(){
  const delta = clock.getDelta();
  const elapsed = clock.getElapsedTime();
  
  // Scan movement
  scanPos += delta * 0.35 * scanDir;
  if(scanPos > 1.8) scanDir = -1;
  if(scanPos < -1.8) scanDir = 1;
  
  // Update scan line and sheet
  scanLine.position.z = scanPos;
  sheet.position.z = scanPos;
  
  // Check for defects
  const currentZ = scanPos;
  scanActive = false;
  currentDefect = null;
  
  for(let d of defects){
    // Map defect angle to position along track
    const defectZ = (d.axle - 1.5) * 0.6;
    if(Math.abs(currentZ - defectZ) < 0.08){
      scanActive = true;
      currentDefect = d;
      break;
    }
  }
  
  // Update defect visibility
  for(let i = 0; i < defectMarkers.length; i++){
    const dm = defectMarkers[i];
    const axleIdx = Math.floor(i / 2);
    const axleZ = (axleIdx - 1.5) * 0.6;
    dm.visible = Math.abs(scanPos - axleZ) < 0.1 && Math.random() < 0.3;
    if(dm.visible){
      // Pulse
      const pulse = 0.5 + 0.5 * Math.sin(elapsed * 4 + i);
      dm.material.emissiveIntensity = pulse * 0.8;
      dm.scale.setScalar(1 + pulse * 0.3);
    }
  }
  
  // Scan status
  if(scanActive){
    scanStatus.classList.add('active');
    scanLineMat.color.setHex(0xff4444);
    scanLineMat.opacity = 0.8;
    sheetMat.color.setHex(0xff4444);
    sheetMat.opacity = 0.15;
    scannerLight.color.setHex(0xff4444);
    
    // Trigger detection
    if(Math.random() < 0.02){
      scanCount++;
      defectCount++;
      carbonTotal += 0.25;
      scanCountEl.textContent = scanCount;
      defectFoundEl.textContent = defectCount;
      carbonTotalEl.textContent = carbonTotal.toFixed(1);
      efficiencyEl.textContent = Math.min(85, Math.floor(carbonTotal / scanCount * 100 + 12)) + '%';
      
      // Detail panel
      dPos.textContent = `轮对${(currentDefect?.axle||0)+1}`;
      dSurface.textContent = '⚠ 缺陷';
      dSurface.className = 'v warn';
      dDefect.textContent = (currentDefect?Math.floor(currentDefect.severity*100):50).toFixed(0)+'%';
      dCarbon.textContent = '0.25 kg';
      
      // Alert light flash
      alertLight.intensity = 1.5;
    }
  } else {
    scanStatus.classList.remove('active');
    scanLineMat.color.setHex(0x00ff88);
    scanLineMat.opacity = 0.4;
    sheetMat.color.setHex(0x00ff88);
    sheetMat.opacity = 0.08;
    scannerLight.color.setHex(0x00ffaa);
    alertLight.intensity *= 0.95;
    
    // Reset detail when not scanning in defect zone
    if(Math.random() < 0.01){
      scanCount++;
      carbonTotal += 0.25;
      scanCountEl.textContent = scanCount;
      carbonTotalEl.textContent = carbonTotal.toFixed(1);
      efficiencyEl.textContent = Math.min(85, Math.floor(carbonTotal / scanCount * 100 + 12)) + '%';
      
      dPos.textContent = `轮对${Math.floor(Math.random()*4)+1}`;
      dSurface.textContent = '✅ 正常';
      dSurface.className = 'v ok';
      dDefect.textContent = '—';
      dCarbon.textContent = '0.25 kg';
    }
  }
  
  // Wheel rotation (slow rotation)
  wheelAngle += delta * 0.5;
  
  // Rotate all wheels in the scene
  // Find all wheel groups and rotate them
  scene.children.forEach(child => {
    if(child.type === 'Group' && (child.children.length > 2)){
      child.children.forEach(sub => {
        if(sub.type === 'Group' && sub.children.length > 3){
          sub.rotation.x += delta * 0.3;
        }
      });
    }
  });
  
  // Rotate wheels in bogies
  [bogie1, bogie2].forEach(bogie => {
    bogie.children.forEach(child => {
      if(child.type === 'Group' && child.position.y < 0.3){
        child.children.forEach(wheel => {
          if(wheel.type === 'Group' && wheel.children.length > 3){
            wheel.rotation.x += delta * 0.3;
          }
        });
      }
    });
  });
  
  // Zoom wheel rotation
  zoomWheel.rotation.z += delta * 0.5;
  
  // Gantry status light pulse
  const statusL = gantry.children.find(c => c.type === 'Mesh' && c.geometry.type === 'SphereGeometry');
  if(statusL){
    const intensity = 0.3 + 0.3 * Math.sin(elapsed * 2);
    statusL.material.emissiveIntensity = intensity;
  }
  
  // Camera slow auto-rotation (when not interacting)
  controls.update();
  
  // Render main scene
  renderer.render(scene, camera);
  
  // Render zoom scene (independent rotation)
  zoomCamera.position.x = 0.5 + 0.15 * Math.sin(elapsed * 0.3);
  zoomCamera.lookAt(0, 0.05, 0);
  zoomRenderer.render(zoomScene, zoomCamera);
  
  requestAnimationFrame(animate);
}

animate();

// ====== Resize Handler ======
window.addEventListener('resize', () => {
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  
  // Resize zoom window
  const zw = zoomContainer.clientWidth;
  const zh = zoomContainer.clientHeight;
  zoomCamera.aspect = zw / zh;
  zoomCamera.updateProjectionMatrix();
  zoomRenderer.setSize(zw, zh);
});

// ====== Analytics Tracking ======
const trackData = {p: window.location.pathname, r: document.referrer, t: navigator.userAgent};
navigator.sendBeacon('/api/track', JSON.stringify(trackData));
fetch('/api/track', {method:'POST', body:JSON.stringify(trackData), headers:{'Content-Type':'application/json'}}).catch(()=>{});

// ====== Click to toggle auto-rotation ======
renderer.domElement.addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate;
  const status = document.getElementById('scan-status');
  if(!controls.autoRotate){
    status.textContent = '⏸ 视角已暂停';
    status.classList.add('active');
    setTimeout(() => {status.textContent = '⚡ 检测扫描中 ...';}, 2000);
  } else {
    status.textContent = '⚡ 检测扫描中 ...';
    status.classList.add('active');
    setTimeout(() => status.classList.remove('active'), 1500);
  }
});
</script>
</body>
</html>"""

@app.get("/")
def index():
    return Response(HTML, media_type="text/html; charset=utf-8")