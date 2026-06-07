"""
万象归踪 — 3D交互模型展示网站（高仿真版v3）
基于参考图重建：真实火车轮对比例 + 完整机车 + 双视口
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

/* Top title */
#title{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:100;text-align:center;pointer-events:none}
#title h1{font-size:24px;font-weight:700;background:linear-gradient(135deg,#34d399,#06b6d4,#60a5fa);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;letter-spacing:3px;text-shadow:0 0 40px rgba(6,182,212,0.3)}
#title p{font-size:12px;color:rgba(255,255,255,0.4);margin-top:4px;letter-spacing:6px}

/* Split layout: main view left, wheel detail right */
#main-view{position:absolute;left:0;top:0;width:70%;height:100vh}
#side-panel{position:absolute;right:0;top:0;width:30%;height:100vh;background:rgba(8,12,26,0.95);
  border-left:1px solid rgba(255,255,255,0.06);display:flex;flex-direction:column;z-index:50}
#side-title{padding:24px 20px 12px;text-align:center}
#side-title h2{font-size:16px;color:#34d399;letter-spacing:2px}
#side-title p{font-size:11px;color:rgba(255,255,255,0.35);margin-top:4px;letter-spacing:1px}

#wheel-detail-container{flex:1;position:relative;min-height:0}
#wheel-detail-container canvas{width:100% !important;height:100% !important}
#wheel-label{position:absolute;top:12px;left:16px;font-size:10px;color:rgba(255,255,255,0.3);letter-spacing:1px;pointer-events:none;z-index:10}

/* Side info cards */
#info-cards{padding:0 16px 20px;display:flex;flex-direction:column;gap:8px}
.info-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px 16px}
.info-card .label{font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:1px;margin-bottom:4px}
.info-card .value{font-size:18px;font-weight:700}
.info-card .value.green{color:#34d399}
.info-card .value.gold{color:#fbbf24}
.info-card .value.rose{color:#fb7185}
.info-card .value.blue{color:#60a5fa}

/* Bottom HUD on main view */
#hud{position:fixed;bottom:24px;left:calc(35% - 200px);transform:translateX(-50%);z-index:100;
  display:flex;gap:20px;background:rgba(10,14,26,0.7);backdrop-filter:blur(12px);padding:14px 28px;border-radius:14px;
  border:1px solid rgba(255,255,255,0.06);}
.hud-item{text-align:center;min-width:70px}
.hud-item .num{font-size:20px;font-weight:700}
.hud-item .num.green{color:#34d399}
.hud-item .num.gold{color:#fbbf24}
.hud-item .num.rose{color:#fb7185}
.hud-item .label{font-size:10px;color:rgba(255,255,255,0.4);margin-top:2px;letter-spacing:1px}
.hud-divider{width:1px;background:rgba(255,255,255,0.08);align-self:stretch}

/* Scan indicator */
#scan-status{position:fixed;left:35%;top:50%;transform:translate(-50%,-50%);z-index:50;
  pointer-events:none;font-size:16px;color:rgba(52,211,153,0.5);letter-spacing:4px;
  opacity:0;transition:opacity 0.3s}
#scan-status.active{opacity:1}

@media(max-width:900px){
  #main-view{width:100%;height:60vh}
  #side-panel{width:100%;height:40vh;top:60vh;border-left:none;border-top:1px solid rgba(255,255,255,0.06)}
  #hud{left:50%;bottom:auto;top:calc(60vh - 50px);transform:translateX(-50%);padding:10px 16px;gap:12px}
  #hud .hud-item .num{font-size:16px}
  #scan-status{left:50%;top:30vh}
  #title h1{font-size:18px}
}
</style>
</head>
<body>
<div id="title"><h1>🚂 万象归踪 · 智能轮对检测</h1><p>3D SIMULATION · 双碳减排驱动铁路低碳运维</p></div>
<div id="scan-status">⚡ 激光扫描检测中 ...</div>
<div id="main-view"><div id="canvas-container"></div></div>
<div id="side-panel">
  <div id="side-title">
    <h2>🔍 轮对剖面分析</h2>
    <p>REAL-TIME WHEEL INSPECTION</p>
  </div>
  <div id="wheel-detail-container">
    <div id="wheel-label">剖面视图 · 踏面检测</div>
  </div>
  <div id="info-cards">
    <div class="info-card">
      <div class="label">轮位状态</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="value green" id="d-pos">轮对 #1</span>
        <span style="font-size:12px;color:rgba(255,255,255,0.5)" id="d-status">✅ 正常</span>
      </div>
    </div>
    <div class="info-card">
      <div class="label">检测数据</div>
      <div style="display:flex;gap:20px">
        <div><span style="font-size:12px;color:rgba(255,255,255,0.5)">踏面磨损</span><br><span class="value green" id="d-wear">0.12 mm</span></div>
        <div><span style="font-size:12px;color:rgba(255,255,255,0.5)">圆度偏差</span><br><span class="value blue" id="d-round">0.08 mm</span></div>
      </div>
    </div>
    <div class="info-card" style="border-color:rgba(52,211,153,0.2);background:rgba(52,211,153,0.04)">
      <div class="label">🌱 碳减排贡献</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="value green" id="d-carbon">12.5 kg</span>
        <span style="font-size:11px;color:rgba(255,255,255,0.4)">/ 次检测</span>
      </div>
    </div>
  </div>
</div>
<div id="hud">
  <div class="hud-item"><div class="num green" id="scan-count">0</div><div class="label">检测轮对</div></div>
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

// ======================================================================
// SCENE SETUP - Main view (left 70%)
// ======================================================================
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e1a);
scene.fog = new THREE.Fog(0x0a0e1a, 40, 80);

const camera = new THREE.PerspectiveCamera(30, container.clientWidth/container.clientHeight, 0.1, 100);
camera.position.set(16, 10, 20);
camera.lookAt(0, 0.3, 0);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.5, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 6;
controls.maxDistance = 40;
controls.maxPolarAngle = Math.PI / 2.05;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.6;
controls.update();

// ======================================================================
// LIGHTING
// ======================================================================
const ambient = new THREE.AmbientLight(0x334466, 0.5);
scene.add(ambient);

const hemi = new THREE.HemisphereLight(0x4488cc, 0x224466, 0.6);
scene.add(hemi);

const dirLight = new THREE.DirectionalLight(0xffeedd, 2.0);
dirLight.position.set(15, 25, 10);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
dirLight.shadow.camera.near = 1;
dirLight.shadow.camera.far = 50;
dirLight.shadow.camera.left = -15;
dirLight.shadow.camera.right = 15;
dirLight.shadow.camera.top = 15;
dirLight.shadow.camera.bottom = -5;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x4488ff, 0.4);
fillLight.position.set(-10, 5, -15);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0x88ccff, 0.6);
rimLight.position.set(0, -8, -20);
scene.add(rimLight);

// Scanner lights
const scannerLight = new THREE.PointLight(0x00ffaa, 1.5, 6);
scannerLight.position.set(0, 0.8, 0);
scene.add(scannerLight);

const alertLight = new THREE.PointLight(0xff4444, 0, 5);
alertLight.position.set(0, 1.5, 0);
scene.add(alertLight);

// ======================================================================
// GROUND & ENVIRONMENT
// ======================================================================
const groundGeo = new THREE.PlaneGeometry(80, 80);
const groundMat = new THREE.MeshStandardMaterial({color:0x0d1117, roughness:0.95, metalness:0.05});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.y = -0.48;
ground.receiveShadow = true;
scene.add(ground);

const gridHelper = new THREE.GridHelper(50, 40, 0x1a2a44, 0x111833);
gridHelper.position.y = -0.44;
scene.add(gridHelper);

// ======================================================================
// REALISTIC TRAIN WHEEL - Proper Chinese railway wheel profile
// ======================================================================
function createTrainWheel(color=0x666666, detailLevel='normal'){
  const group = new THREE.Group();
  
  // Realistic wheel profile for Chinese railway (standard wheel diameter ~920mm)
  // Scale: 1 unit = ~1m. Wheel radius = 0.46 units (920mm diameter)
  // Profile defines cross-section from flange tip (outer) to hub center (inner)
  
  const R = 0.46; // Wheel radius in units (realistic: 920mm diameter)
  
  // Cross-section points for a real railway wheel
  // x = radial distance from center, y = vertical position on cross-section
  // The profile goes from outer flange tip, along tread, through web plate, to hub
  const pts = [];
  
  // === FLANGE (highest point - keeps wheel on rail) ===
  // Flange tip - outermost and highest point
  pts.push(new THREE.Vector2(R * 1.0, R * 0.52));      // Flange face outer edge
  pts.push(new THREE.Vector2(R * 0.97, R * 0.55));     // Flange tip (highest)
  pts.push(new THREE.Vector2(R * 0.94, R * 0.53));     // Flange back slope start
  pts.push(new THREE.Vector2(R * 0.90, R * 0.48));     // Flange back
  pts.push(new THREE.Vector2(R * 0.87, R * 0.42));     // Flange throat (transition to tread)
  
  // === TREAD (running surface that contacts rail) ===
  pts.push(new THREE.Vector2(R * 0.85, R * 0.36));     // Tread start (flange root)
  pts.push(new THREE.Vector2(R * 0.83, R * 0.28));     // Tread outer
  pts.push(new THREE.Vector2(R * 0.80, R * 0.18));     // Tread middle (1:20 taper)
  pts.push(new THREE.Vector2(R * 0.76, R * 0.08));     // Tread inner
  pts.push(new THREE.Vector2(R * 0.72, R * 0.02));     // Tread taper end
  
  // === INNER RIM FACE ===
  pts.push(new THREE.Vector2(R * 0.65, R * 0.0));      // Inner rim edge
  pts.push(new THREE.Vector2(R * 0.55, R * 0.0));      // Inner rim face
  
  // === WEB PLATE (thin plate connecting rim to hub) ===
  pts.push(new THREE.Vector2(R * 0.45, R * -0.01));    // Web outer (thick)
  pts.push(new THREE.Vector2(R * 0.35, R * -0.03));    // Web mid
  pts.push(new THREE.Vector2(R * 0.25, R * -0.05));    // Web thin
  pts.push(new THREE.Vector2(R * 0.18, R * -0.06));    // Web inner
  
  // === HUB (center section with axle hole) ===
  pts.push(new THREE.Vector2(R * 0.14, R * -0.06));    // Hub outer
  pts.push(new THREE.Vector2(R * 0.10, R * -0.05));    // Hub face
  pts.push(new THREE.Vector2(R * 0.07, R * -0.04));    // Hub inner taper
  pts.push(new THREE.Vector2(R * 0.04, R * -0.02));    // Hub near-axle
  
  // ===== Build full cross-section (both top and bottom halves) =====
  const profile = [];
  // Copy all points as-is (top half of cross-section)
  for(let p of pts) profile.push(new THREE.Vector2(p.x, p.y));
  // Mirror to bottom half (reversed order)
  for(let i=pts.length-1; i>=0; i--){
    const p = pts[i];
    profile.push(new THREE.Vector2(p.x, -p.y));
  }
  // Close the loop back to first point
  profile.push(new THREE.Vector2(pts[0].x, pts[0].y));
  
  // Choose material based on detail level
  let wheelMat;
  if(detailLevel === 'high'){
    wheelMat = new THREE.MeshStandardMaterial({
      color: color, metalness: 0.75, roughness: 0.35,
      side: THREE.DoubleSide, envMapIntensity: 0.5
    });
  } else {
    wheelMat = new THREE.MeshStandardMaterial({
      color: color, metalness: 0.7, roughness: 0.4,
      side: THREE.DoubleSide
    });
  }
  
  const wheelGeo = new THREE.LatheGeometry(profile, 48);
  const wheel = new THREE.Mesh(wheelGeo, wheelMat);
  wheel.castShadow = true;
  wheel.receiveShadow = true;
  group.add(wheel);
  
  // Add tire/rim ring detail - subtle groove on tread
  const tireMat = new THREE.MeshStandardMaterial({
    color: 0x888888, metalness: 0.85, roughness: 0.25
  });
  const tireRing = new THREE.Mesh(
    new THREE.TorusGeometry(R * 0.82, 0.008, 6, 48),
    tireMat
  );
  tireRing.rotation.x = Math.PI/2;
  tireRing.position.y = R * 0.08;
  group.add(tireRing);
  
  // Brake disc
  const discMat = new THREE.MeshStandardMaterial({
    color: 0x3a3a3a, metalness: 0.5, roughness: 0.7
  });
  
  // Brake disc on each side
  for(let side of [-1, 1]){
    const discGroup = new THREE.Group();
    
    // Main disc
    const disc = new THREE.Mesh(
      new THREE.CylinderGeometry(R*0.32, R*0.32, 0.025, 32),
      discMat
    );
    disc.position.x = side * 0.55;
    disc.rotation.z = Math.PI/2;
    discGroup.add(disc);
    
    // Brake pad contact surface (slightly raised ring)
    const padMat = new THREE.MeshStandardMaterial({
      color: 0x555555, metalness: 0.6, roughness: 0.8
    });
    const padRing = new THREE.Mesh(
      new THREE.TorusGeometry(R*0.28, 0.01, 8, 32),
      padMat
    );
    padRing.position.x = side * 0.57;
    padRing.rotation.y = Math.PI/2;
    discGroup.add(padRing);
    
    // Ventilation holes
    for(let i = 0; i < 8; i++){
      const angle = (i / 8) * Math.PI * 2;
      const hole = new THREE.Mesh(
        new THREE.CylinderGeometry(0.012, 0.012, 0.03, 6),
        new THREE.MeshStandardMaterial({color: 0x1a1a1a})
      );
      hole.position.set(
        side * 0.55,
        Math.cos(angle) * R*0.2,
        Math.sin(angle) * R*0.2
      );
      hole.rotation.z = side > 0 ? Math.PI/3 : -Math.PI/3;
      discGroup.add(hole);
    }
    
    group.add(discGroup);
  }
  
  // Center hub detail
  const hubMat = new THREE.MeshStandardMaterial({
    color: 0x444444, metalness: 0.8, roughness: 0.3
  });
  const hubCap = new THREE.Mesh(
    new THREE.CylinderGeometry(R*0.06, R*0.08, 0.06, 12),
    hubMat
  );
  hubCap.position.set(0, 0, 0);
  group.add(hubCap);
  
  return group;
}

// ======================================================================
// BUILD WHEELSET (2 wheels + axle)
// ======================================================================
function createWheelset(xPos=0, color=0x666666){
  const group = new THREE.Group();
  const R = 0.46;
  const GAUGE = 1.435; // Standard gauge in meters
  
  // Left wheel
  const leftWheel = createTrainWheel(color);
  leftWheel.position.z = -GAUGE/2;
  leftWheel.position.x = 0;
  group.add(leftWheel);
  
  // Right wheel
  const rightWheel = createTrainWheel(color);
  rightWheel.position.z = GAUGE/2;
  rightWheel.position.x = 0;
  group.add(rightWheel);
  
  // Axle
  const axleMat = new THREE.MeshStandardMaterial({
    color: 0x3a3a3a, metalness: 0.8, roughness: 0.3
  });
  const axle = new THREE.Mesh(
    new THREE.CylinderGeometry(0.06, 0.06, GAUGE + 0.1, 12),
    axleMat
  );
  axle.rotation.z = Math.PI/2;
  group.add(axle);
  
  // Gearbox on axle
  const gearMat = new THREE.MeshStandardMaterial({
    color: 0x2a2a2a, metalness: 0.6, roughness: 0.5
  });
  const gearbox = new THREE.Mesh(
    new THREE.BoxGeometry(0.15, 0.12, 0.18),
    gearMat
  );
  gearbox.position.set(0, -R*0.1, -GAUGE/4);
  group.add(gearbox);
  
  // Primary suspension spring
  const springMat = new THREE.MeshStandardMaterial({
    color: 0x444444, metalness: 0.3, roughness: 0.5
  });
  for(let z of [-GAUGE/2, GAUGE/2]){
    const spring = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.05, 0.12, 8),
      springMat
    );
    spring.position.set(0, R + 0.06, z);
    group.add(spring);
  }
  
  group.position.x = xPos;
  group.position.y = 0.02; // Lift slightly above rail
  return group;
}

// ======================================================================
// BUILD BOGIE (2 wheelsets + frame)
// ======================================================================
function createBogie(xPos=0, color=0x666666){
  const group = new THREE.Group();
  const R = 0.46;
  const GAUGE = 1.435;
  const WHEELBASE = 2.5; // Distance between axles in meters
  
  // Bogie frame
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x2a2a2a, metalness: 0.5, roughness: 0.6
  });
  const frameMat2 = new THREE.MeshStandardMaterial({
    color: 0x333333, metalness: 0.4, roughness: 0.5
  });
  
  // Side frames (2 longitudinal beams)
  for(let z of [-GAUGE/2 + 0.15, GAUGE/2 - 0.15]){
    const sideBeam = new THREE.Mesh(
      new THREE.BoxGeometry(0.12, 0.08, WHEELBASE + 0.2),
      frameMat
    );
    sideBeam.position.set(0, R + 0.15, z);
    group.add(sideBeam);
  }
  
  // Cross beams
  for(let z of [-WHEELBASE/3, WHEELBASE/3]){
    const cross = new THREE.Mesh(
      new THREE.BoxGeometry(GAUGE - 0.3, 0.06, 0.12),
      frameMat2
    );
    cross.position.set(0, R + 0.18, z);
    group.add(cross);
  }
  
  // Center pivot (where bogie connects to car body)
  const pivotMat = new THREE.MeshStandardMaterial({
    color: 0x444444, metalness: 0.6, roughness: 0.4
  });
  const pivot = new THREE.Mesh(
    new THREE.CylinderGeometry(0.1, 0.12, 0.08, 12),
    pivotMat
  );
  pivot.position.set(0, R + 0.30, 0);
  group.add(pivot);
  
  // Axle bearing boxes
  const bearingMat = new THREE.MeshStandardMaterial({
    color: 0x555555, metalness: 0.7, roughness: 0.3
  });
  for(let z of [-WHEELBASE/2, WHEELBASE/2]){
    for(let side of [-1, 1]){
      const bearing = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.06, 0.06),
        bearingMat
      );
      bearing.position.set(side * (GAUGE/2 - 0.1), R + 0.10, z);
      group.add(bearing);
    }
  }
  
  // Two wheelsets
  const ws1 = createWheelset(-WHEELBASE/2, color);
  group.add(ws1);
  
  const ws2 = createWheelset(WHEELBASE/2, color);
  group.add(ws2);
  
  // Secondary suspension (coil springs between bogie and car body)
  const springMat = new THREE.MeshStandardMaterial({
    color: 0x3a3a3a, metalness: 0.3, roughness: 0.5
  });
  for(let z of [-WHEELBASE/4, WHEELBASE/4]){
    for(let side of [-1, 1]){
      const spring = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.05, 0.14, 8),
        springMat
      );
      spring.position.set(side * (GAUGE/2 - 0.3), R + 0.28, z);
      group.add(spring);
    }
  }
  
  group.position.x = xPos;
  group.position.y = 0.02;
  return group;
}

// ======================================================================
// BUILD LOCOMOTIVE BODY - Chinese electric locomotive
// ======================================================================
function createLocomotive(){
  const group = new THREE.Group();
  const R = 0.46;
  
  // Colors
  const bodyBlue = 0x1a3a6a;
  const bodyLight = 0x224488;
  const accentRed = 0xc41e3a;
  const roofGray = 0xcccccc;
  const darkGray = 0x222222;
  const glassColor = 0x88ccff;
  
  const bodyMat = new THREE.MeshStandardMaterial({color: bodyBlue, metalness: 0.3, roughness: 0.4, envMapIntensity: 0.3});
  const bodyMat2 = new THREE.MeshStandardMaterial({color: bodyLight, metalness: 0.25, roughness: 0.5});
  const accentMat = new THREE.MeshStandardMaterial({color: accentRed, metalness: 0.2, roughness: 0.5});
  const cabMat = new THREE.MeshStandardMaterial({color: 0x0d1f3c, metalness: 0.3, roughness: 0.3});
  const roofMat = new THREE.MeshStandardMaterial({color: roofGray, metalness: 0.1, roughness: 0.6});
  const darkMat = new THREE.MeshStandardMaterial({color: darkGray, metalness: 0.5, roughness: 0.5});
  const glassMat = new THREE.MeshStandardMaterial({
    color: glassColor, metalness: 0.95, roughness: 0.05,
    transparent: true, opacity: 0.25, envMapIntensity: 1.0
  });
  const detailMat = new THREE.MeshStandardMaterial({color: 0xdddddd, metalness: 0.4, roughness: 0.3});
  const underMat = new THREE.MeshStandardMaterial({color: 0x1a1a1a, metalness: 0.2, roughness: 0.7});
  
  // === MAIN BODY (center section) ===
  const bodyLength = 4.5;
  const bodyWidth = 0.9;
  const bodyHeight = 0.7;
  const bodyY = R + bodyHeight/2 + 0.35;
  
  // Main carbody
  const mainBody = new THREE.Mesh(
    new THREE.BoxGeometry(bodyWidth, bodyHeight, bodyLength),
    bodyMat
  );
  mainBody.position.y = bodyY;
  mainBody.castShadow = true;
  mainBody.receiveShadow = true;
  group.add(mainBody);
  
  // Body side panels (slightly raised for 3D effect)
  for(let side of [-1, 1]){
    const panel = new THREE.Mesh(
      new THREE.BoxGeometry(0.01, bodyHeight - 0.1, bodyLength - 0.4),
      bodyMat2
    );
    panel.position.set(side * (bodyWidth/2 + 0.01), bodyY, 0);
    group.add(panel);
  }
  
  // === CAB (front) ===
  const cabY = bodyY + bodyHeight/2 + 0.2;
  const cab = new THREE.Mesh(
    new THREE.BoxGeometry(bodyWidth * 0.85, 0.5, 1.1),
    cabMat
  );
  cab.position.set(0, cabY + 0.15, bodyLength/2 + 0.35);
  cab.castShadow = true;
  group.add(cab);
  
  // Cab front windshield
  const windshield = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.3, 0.03),
    glassMat
  );
  windshield.position.set(0, cabY + 0.2, bodyLength/2 + 0.92);
  group.add(windshield);
  
  // Cab side windows
  for(let side of [-1, 1]){
    const sideWin = new THREE.Mesh(
      new THREE.BoxGeometry(0.03, 0.2, 0.35),
      glassMat
    );
    sideWin.position.set(side * (bodyWidth/2 + 0.02), cabY + 0.2, bodyLength/2 + 0.5);
    group.add(sideWin);
  }
  
  // === REAR CAB (symmetric) ===
  const rearCab = cab.clone();
  rearCab.position.z = -(bodyLength/2 + 0.35);
  group.add(rearCab);
  
  const rearWin = windshield.clone();
  rearWin.position.z = -(bodyLength/2 + 0.92);
  group.add(rearWin);
  
  // === ROOF ===
  const roof = new THREE.Mesh(
    new THREE.BoxGeometry(bodyWidth * 0.85, 0.04, bodyLength - 0.2),
    roofMat
  );
  roof.position.y = bodyY + bodyHeight/2 + 0.02;
  group.add(roof);
  
  // Roof equipment (insulators, cooling units, etc.)
  const equipPositions = [-1.5, -0.5, 0.5, 1.5];
  for(let z of equipPositions){
    const unit = new THREE.Mesh(
      new THREE.BoxGeometry(0.5, 0.1, 0.4),
      detailMat
    );
    unit.position.set(0, bodyY + bodyHeight/2 + 0.09, z);
    group.add(unit);
    
    // Small detail on top
    const detail = new THREE.Mesh(
      new THREE.BoxGeometry(0.3, 0.04, 0.2),
      new THREE.MeshStandardMaterial({color: 0x999999, metalness: 0.3, roughness: 0.4})
    );
    detail.position.set(0, bodyY + bodyHeight/2 + 0.16, z);
    group.add(detail);
  }
  
  // === PANTOGRAPH (simplified but recognizable) ===
  const pantoBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.25, 0.04, 0.3),
    detailMat
  );
  pantoBase.position.set(0, bodyY + bodyHeight/2 + 0.08, -1.8);
  group.add(pantoBase);
  
  // Main arm
  const armMat = new THREE.MeshStandardMaterial({color: 0xaaaaaa, metalness: 0.4, roughness: 0.3});
  const pantoArm = new THREE.Mesh(
    new THREE.BoxGeometry(0.025, 0.35, 0.025),
    armMat
  );
  pantoArm.position.set(0, bodyY + bodyHeight/2 + 0.27, -1.8);
  group.add(pantoArm);
  
  // Upper arm (angled)
  const upperArm = new THREE.Mesh(
    new THREE.BoxGeometry(0.02, 0.25, 0.02),
    armMat
  );
  upperArm.position.set(0.08, bodyY + bodyHeight/2 + 0.42, -1.8);
  upperArm.rotation.z = 0.2;
  group.add(upperArm);
  
  // Contact strip
  const stripMat = new THREE.MeshStandardMaterial({color: 0x888888, metalness: 0.8, roughness: 0.2});
  const contactStrip = new THREE.Mesh(
    new THREE.BoxGeometry(0.7, 0.02, 0.025),
    stripMat
  );
  contactStrip.position.set(0, bodyY + bodyHeight/2 + 0.55, -1.8);
  group.add(contactStrip);
  
  // === RED ACCENT STRIPES ===
  for(let side of [-1, 1]){
    // Lower stripe
    const stripe1 = new THREE.Mesh(
      new THREE.BoxGeometry(0.02, 0.04, bodyLength - 0.3),
      accentMat
    );
    stripe1.position.set(side * (bodyWidth/2 + 0.005), bodyY - bodyHeight/3, 0);
    group.add(stripe1);
    
    // Upper stripe
    const stripe2 = new THREE.Mesh(
      new THREE.BoxGeometry(0.02, 0.03, bodyLength - 0.3),
      accentMat
    );
    stripe2.position.set(side * (bodyWidth/2 + 0.005), bodyY + bodyHeight/3, 0);
    group.add(stripe2);
  }
  
  // === HEADLIGHTS ===
  const lightMat = new THREE.MeshStandardMaterial({
    color: 0xffeecc, emissive: 0xffaa44, emissiveIntensity: 0.3
  });
  const lightFrameMat = new THREE.MeshStandardMaterial({color: 0x555555, metalness: 0.4, roughness: 0.3});
  
  for(let x of [-0.2, 0.2]){
    const frame = new THREE.Mesh(
      new THREE.CircleGeometry(0.1, 16),
      lightFrameMat
    );
    frame.position.set(x, bodyY - 0.15, bodyLength/2 + 0.02);
    frame.rotation.y = Math.PI/2;
    group.add(frame);
    
    const light = new THREE.Mesh(
      new THREE.CircleGeometry(0.07, 16),
      lightMat
    );
    light.position.set(x, bodyY - 0.15, bodyLength/2 + 0.03);
    light.rotation.y = Math.PI/2;
    group.add(light);
  }
  
  // === COUPLERS ===
  const couplerMat = new THREE.MeshStandardMaterial({color: 0x444444, metalness: 0.7, roughness: 0.4});
  for(let z of [bodyLength/2 + 0.05, -(bodyLength/2 + 0.05)]){
    const coupler = new THREE.Mesh(
      new THREE.BoxGeometry(0.12, 0.08, 0.2),
      couplerMat
    );
    coupler.position.set(0, bodyY - bodyHeight/2 - 0.15, z);
    group.add(coupler);
    
    const hook = new THREE.Mesh(
      new THREE.TorusGeometry(0.04, 0.015, 6, 8),
      couplerMat
    );
    hook.position.set(0, bodyY - bodyHeight/2 - 0.12, z + 0.12 * Math.sign(z));
    hook.rotation.x = Math.PI/2;
    group.add(hook);
  }
  
  // === UNDERCARRIAGE ===
  const underFrame = new THREE.Mesh(
    new THREE.BoxGeometry(bodyWidth - 0.1, 0.1, bodyLength - 0.3),
    underMat
  );
  underFrame.position.y = bodyY - bodyHeight/2 - 0.05;
  group.add(underFrame);
  
  // Side steps
  for(let side of [-1, 1]){
    for(let z of [-1.2, 0, 1.2]){
      const step = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.015, 0.3),
        darkMat
      );
      step.position.set(side * (bodyWidth/2 + 0.06), bodyY - bodyHeight/2 - 0.08, z);
      group.add(step);
    }
  }
  
  // === VENTILATION GRILLES (side details) ===
  const grilleMat = new THREE.MeshStandardMaterial({color: 0x1a2a4a, metalness: 0.2, roughness: 0.6});
  for(let side of [-1, 1]){
    for(let z of [-0.8, 0.8]){
      const grille = new THREE.Mesh(
        new THREE.BoxGeometry(0.01, 0.3, 0.8),
        grilleMat
      );
      grille.position.set(side * (bodyWidth/2 + 0.005), bodyY, z);
      group.add(grille);
      
      // Grille slats
      const slatMat = new THREE.MeshStandardMaterial({color: 0x2a3a5a, metalness: 0.3, roughness: 0.5});
      for(let s = -3; s <= 3; s++){
        const slat = new THREE.Mesh(
          new THREE.BoxGeometry(0.01, 0.005, 0.7),
          slatMat
        );
        slat.position.set(side * (bodyWidth/2 + 0.008), bodyY + s * 0.04, z);
        group.add(slat);
      }
    }
  }
  
  return group;
}

// ======================================================================
// BUILD TRACK
// ======================================================================
function createTrack(trackLength=12){
  const group = new THREE.Group();
  
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x888888, metalness: 0.9, roughness: 0.2, envMapIntensity: 0.3
  });
  const sleeperMat = new THREE.MeshStandardMaterial({
    color: 0x5a3d2b, roughness: 0.95
  });
  const ballastMat = new THREE.MeshStandardMaterial({
    color: 0x3a3028, roughness: 1.0
  });
  const railTopMat = new THREE.MeshStandardMaterial({
    color: 0x999999, metalness: 0.95, roughness: 0.15
  });
  
  const GAUGE = 1.435;
  
  // Ballast bed
  const ballast = new THREE.Mesh(
    new THREE.BoxGeometry(1.8, 0.05, trackLength),
    ballastMat
  );
  ballast.position.set(0, -0.44, 0);
  group.add(ballast);
  
  // Sleepers
  const sleeperCount = Math.floor(trackLength / 0.35);
  for(let i = 0; i < sleeperCount; i++){
    const z = -trackLength/2 + i * 0.35 + 0.15;
    const sleeper = new THREE.Mesh(
      new THREE.BoxGeometry(1.1, 0.04, 0.1),
      sleeperMat
    );
    sleeper.position.set(0, -0.38, z);
    group.add(sleeper);
  }
  
  // Rails (I-beam profile simplified)
  for(let side of [-1, 1]){
    const x = side * GAUGE/2;
    
    // Rail foot (base)
    const foot = new THREE.Mesh(
      new THREE.BoxGeometry(0.08, 0.025, trackLength),
      railMat
    );
    foot.position.set(x, -0.34, 0);
    group.add(foot);
    
    // Rail web
    const web = new THREE.Mesh(
      new THREE.BoxGeometry(0.03, 0.065, trackLength),
      railMat
    );
    web.position.set(x, -0.295, 0);
    group.add(web);
    
    // Rail head (top running surface - rounded shape)
    const head = new THREE.Mesh(
      new THREE.BoxGeometry(0.05, 0.025, trackLength),
      railTopMat
    );
    head.position.set(x, -0.25, 0);
    group.add(head);
    
    // Rail head top (slightly rounded)
    const headTop = new THREE.Mesh(
      new THREE.BoxGeometry(0.035, 0.01, trackLength),
      new THREE.MeshStandardMaterial({color: 0xaaaaaa, metalness: 0.95, roughness: 0.1})
    );
    headTop.position.set(x, -0.232, 0);
    group.add(headTop);
  }
  
  group.position.y = 0;
  return group;
}

// ======================================================================
// BUILD INSPECTION GANTRY
// ======================================================================
function createGantry(){
  const group = new THREE.Group();
  const GAUGE = 1.435;
  
  const gantryMat = new THREE.MeshStandardMaterial({
    color: 0x2288cc, metalness: 0.5, roughness: 0.3
  });
  const gantryMat2 = new THREE.MeshStandardMaterial({
    color: 0x1166aa, metalness: 0.4, roughness: 0.4
  });
  const laserMat = new THREE.MeshStandardMaterial({
    color: 0x00ffaa, emissive: 0x00ffaa, emissiveIntensity: 0.5,
    transparent: true, opacity: 0.3
  });
  const statusMat = new THREE.MeshStandardMaterial({
    color: 0x00ff88, emissive: 0x00ff88, emissiveIntensity: 0.5
  });
  
  // Side pillars
  for(let side of [-1, 1]){
    const pillar = new THREE.Mesh(
      new THREE.BoxGeometry(0.08, 1.0, 0.08),
      gantryMat2
    );
    pillar.position.set(side * (GAUGE/2 + 0.25), 0.5, 0);
    group.add(pillar);
  }
  
  // Top beam
  const beam = new THREE.Mesh(
    new THREE.BoxGeometry(GAUGE + 0.7, 0.05, 0.12),
    gantryMat
  );
  beam.position.set(0, 1.0, 0);
  group.add(beam);
  
  // Diagonal braces
  for(let side of [-1, 1]){
    const brace = new THREE.Mesh(
      new THREE.BoxGeometry(0.03, 0.5, 0.03),
      gantryMat2
    );
    brace.position.set(side * (GAUGE/2 - 0.1), 0.6, 0);
    brace.rotation.z = side * 0.4;
    group.add(brace);
  }
  
  // Camera array (2D line scan cameras)
  const camMat = new THREE.MeshStandardMaterial({
    color: 0x333333, metalness: 0.5, roughness: 0.4
  });
  const lensMat = new THREE.MeshStandardMaterial({
    color: 0x00ff88, emissive: 0x00ff88, emissiveIntensity: 0.3
  });
  
  // Array of cameras along beam
  for(let side of [-1, 1]){
    for(let i = -2; i <= 2; i++){
      const cam = new THREE.Mesh(
        new THREE.BoxGeometry(0.04, 0.08, 0.06),
        camMat
      );
      cam.position.set(side * (GAUGE/2 - 0.05), 0.55, i * 0.12);
      group.add(cam);
      
      const lens = new THREE.Mesh(
        new THREE.CircleGeometry(0.02, 8),
        lensMat
      );
      lens.position.set(side * (GAUGE/2 - 0.08), 0.55, i * 0.12);
      lens.rotation.y = side > 0 ? -Math.PI/2 : Math.PI/2;
      group.add(lens);
    }
  }
  
  // Laser line generator
  const laserBar = new THREE.Mesh(
    new THREE.BoxGeometry(GAUGE + 0.3, 0.008, 0.008),
    laserMat
  );
  laserBar.position.set(0, 0.22, 0);
  group.add(laserBar);
  
  // Status indicator on top
  const statusLight = new THREE.Mesh(
    new THREE.SphereGeometry(0.04, 8, 8),
    statusMat
  );
  statusLight.position.set(0, 1.05, 0);
  group.add(statusLight);
  
  // Side marker lights
  for(let side of [-1, 1]){
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.015, 6, 6),
      new THREE.MeshStandardMaterial({color: 0xff4444, emissive: 0xff2222, emissiveIntensity: 0.2})
    );
    marker.position.set(side * (GAUGE/2 + 0.28), 0.2, 0);
    group.add(marker);
  }
  
  return group;
}

// ======================================================================
// SECOND SCENE: Wheel Zoom View (right side panel)
// ======================================================================
const zoomContainer = document.getElementById('wheel-detail-container');
const zoomScene = new THREE.Scene();
zoomScene.background = new THREE.Color(0x080c1a);

const zoomCamera = new THREE.PerspectiveCamera(25, zoomContainer.clientWidth/zoomContainer.clientHeight, 0.01, 10);
zoomCamera.position.set(0.8, 0.4, 1.8);
zoomCamera.lookAt(0, 0.05, 0);

const zoomRenderer = new THREE.WebGLRenderer({antialias:true});
zoomRenderer.setSize(zoomContainer.clientWidth, zoomContainer.clientHeight);
zoomRenderer.setPixelRatio(Math.min(devicePixelRatio, 2));
zoomRenderer.toneMapping = THREE.ACESFilmicToneMapping;
zoomRenderer.toneMappingExposure = 1.2;
zoomContainer.appendChild(zoomRenderer.domElement);

// Zoom scene lighting
const zAmbient = new THREE.AmbientLight(0x446688, 0.6);
zoomScene.add(zAmbient);
const zDir = new THREE.DirectionalLight(0xffffff, 2.5);
zDir.position.set(2, 3, 2);
zoomScene.add(zDir);
const zFill = new THREE.DirectionalLight(0x4488ff, 0.5);
zFill.position.set(-1, 1, -1);
zoomScene.add(zFill);

// Create high-detail wheel for zoom view
const R = 0.46;
const zoomWheel = createTrainWheel(0x8899aa, 'high');
zoomWheel.scale.set(1.0, 1.0, 1.0);
zoomWheel.position.set(0, 0.02, 0);
zoomWheel.rotation.x = Math.PI/2;
zoomScene.add(zoomWheel);

// Rail section in zoom view
const zRailMat = new THREE.MeshStandardMaterial({color: 0x999999, metalness: 0.9, roughness: 0.2});
for(let side of [-1, 1]){
  const x = side * 0.72;
  const rail = new THREE.Mesh(
    new THREE.BoxGeometry(0.025, 0.08, 0.6),
    zRailMat
  );
  rail.position.set(x, -0.30, 0);
  zoomScene.add(rail);
}

// Wheel flange indicator (highlight)
const flangeHL = new THREE.Mesh(
  new THREE.TorusGeometry(R * 0.95, 0.004, 8, 48),
  new THREE.MeshStandardMaterial({
    color: 0x00ff88, emissive: 0x00ff88, emissiveIntensity: 0.2,
    transparent: true, opacity: 0.4
  })
);
flangeHL.rotation.x = Math.PI/2;
flangeHL.position.y = R * 0.48;
zoomScene.add(flangeHL);

// Tread measurement line
const treadLine = new THREE.Mesh(
  new THREE.TorusGeometry(R * 0.80, 0.003, 6, 48),
  new THREE.MeshStandardMaterial({
    color: 0x60a5fa, emissive: 0x60a5fa, emissiveIntensity: 0.15,
    transparent: true, opacity: 0.5
  })
);
treadLine.rotation.x = Math.PI/2;
treadLine.position.y = R * 0.15;
zoomScene.add(treadLine);

// Grid in zoom
const zGrid = new THREE.GridHelper(1.2, 10, 0x1a2a44, 0x0f1a33);
zGrid.position.y = -0.40;
zoomScene.add(zGrid);

// ======================================================================
// SCENE ASSEMBLY
// ======================================================================
const GAUGE = 1.435;
const WHEELBASE = 2.5;

// Track
const track = createTrack(12);
scene.add(track);

// Locomotive (positioned on track)
const loco = createLocomotive();
loco.position.set(0, 0.02, 0);
scene.add(loco);

// Bogies
const bogie1 = createBogie(-1.25);
scene.add(bogie1);
const bogie2 = createBogie(1.25);
scene.add(bogie2);

// Inspection gantry (positioned near front of locomotive)
const gantry = createGantry();
gantry.position.set(0, 0, 3.5);
scene.add(gantry);

// Short track section under gantry
const gantryTrack = createTrack(3);
gantryTrack.position.set(0, 0, 3.5);
scene.add(gantryTrack);

// ======================================================================
// SCAN ANIMATION
// ======================================================================
let scanPos = 2.0;
let scanDir = 1;
let isDefect = false;
let scanCount = 0;
let defectCount = 0;
let carbonTotal = 0;
let wheelAngle = 0;
let scanActive = false;

// Scan line (laser sheet)
const scanLineMat = new THREE.MeshBasicMaterial({
  color: 0x00ff88, transparent: true, opacity: 0.4
});
const scanLine = new THREE.Mesh(
  new THREE.BoxGeometry(GAUGE + 0.2, 0.003, 0.003),
  scanLineMat
);
scanLine.position.set(0, 0.22, scanPos);
scene.add(scanLine);

// Laser sheet (transparent plane)
const sheetMat = new THREE.MeshBasicMaterial({
  color: 0x00ff88, transparent: true, opacity: 0.06, side: THREE.DoubleSide
});
const sheet = new THREE.Mesh(
  new THREE.PlaneGeometry(GAUGE + 0.5, 0.6),
  sheetMat
);
sheet.rotation.x = Math.PI/2;
sheet.position.set(0, 0.35, scanPos);
scene.add(sheet);

// Defect markers
const defectMarkers = [];
for(let i = 0; i < 8; i++){
  const dm = new THREE.Mesh(
    new THREE.SphereGeometry(0.015, 8, 8),
    new THREE.MeshStandardMaterial({color:0xff4444, emissive:0xff2222, emissiveIntensity:0.3})
  );
  dm.visible = false;
  dm.position.set(0, 0.4, 0);
  scene.add(dm);
  defectMarkers.push(dm);
}

// ======================================================================
// UI ELEMENTS
// ======================================================================
const scanCountEl = document.getElementById('scan-count');
const defectFoundEl = document.getElementById('defect-found');
const carbonTotalEl = document.getElementById('carbon-total');
const efficiencyEl = document.getElementById('efficiency');
const scanStatus = document.getElementById('scan-status');
const dPos = document.getElementById('d-pos');
const dStatus = document.getElementById('d-status');
const dWear = document.getElementById('d-wear');
const dRound = document.getElementById('d-round');
const dCarbon = document.getElementById('d-carbon');

// ======================================================================
// ANIMATION LOOP
// ======================================================================
const clock = new THREE.Clock();

// Defect simulation
const defects = [];
for(let i = 0; i < 4; i++){
  defects.push({
    axle: Math.floor(Math.random() * 4),
    severity: 0.2 + Math.random() * 0.6
  });
}
let defectAnimPhase = 0;

function animate(){
  const delta = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.getElapsedTime();
  
  // Scan movement
  scanPos += delta * 0.25 * scanDir;
  if(scanPos > 3.8) scanDir = -1;
  if(scanPos < -3.8) scanDir = 1;
  
  // Update scan line and sheet
  scanLine.position.z = scanPos;
  sheet.position.z = scanPos;
  
  // Check for defects (simulate detection)
  scanActive = Math.abs(scanPos) < 0.5;
  
  // Scan status
  if(scanActive){
    scanStatus.classList.add('active');
    scanLineMat.color.setHex(0xff4444);
    scanLineMat.opacity = 0.7;
    sheetMat.color.setHex(0xff4444);
    sheetMat.opacity = 0.12;
    scannerLight.color.setHex(0xff4444);
    
    if(Math.random() < 0.015){
      scanCount++;
      defectCount += Math.random() < 0.3 ? 1 : 0;
      carbonTotal += 0.25;
      scanCountEl.textContent = scanCount;
      defectFoundEl.textContent = defectCount;
      carbonTotalEl.textContent = carbonTotal.toFixed(1);
      efficiencyEl.textContent = Math.min(88, Math.floor(40 + elapsed * 0.1)) + '%';
      
      dPos.textContent = '轮对 #' + (Math.floor(Math.random() * 4) + 1);
      dStatus.textContent = Math.random() < 0.3 ? '⚠ 异常' : '✅ 正常';
      dStatus.style.color = Math.random() < 0.3 ? '#fbbf24' : '#34d399';
      dWear.textContent = (0.05 + Math.random() * 0.3).toFixed(2) + ' mm';
      dRound.textContent = (0.02 + Math.random() * 0.15).toFixed(2) + ' mm';
      dCarbon.textContent = (10 + Math.random() * 5).toFixed(1) + ' kg';
      
      alertLight.intensity = Math.random() < 0.3 ? 1.5 : 0;
    }
  } else {
    scanStatus.classList.remove('active');
    scanLineMat.color.setHex(0x00ff88);
    scanLineMat.opacity = 0.35;
    sheetMat.color.setHex(0x00ff88);
    sheetMat.opacity = 0.06;
    scannerLight.color.setHex(0x00ffaa);
    alertLight.intensity *= 0.95;
    
    if(Math.random() < 0.005){
      scanCount++;
      carbonTotal += 0.25;
      scanCountEl.textContent = scanCount;
      carbonTotalEl.textContent = carbonTotal.toFixed(1);
      efficiencyEl.textContent = Math.min(88, Math.floor(40 + elapsed * 0.1)) + '%';
    }
  }
  
  // Rotate wheels in scene
  function rotateWheels(obj){
    if(obj.type === 'Mesh' && obj.geometry && obj.geometry.type === 'LatheGeometry'){
      obj.parent.rotation.x += delta * 0.5;
    }
    if(obj.children){
      for(let c of obj.children) rotateWheels(c);
    }
  }
  
  // Rotate all wheel meshes
  wheelAngle += delta * 0.5;
  
  // Find and rotate wheels in scene
  function findAndRotateWheels(obj){
    if(!obj.children) return;
    for(let child of obj.children){
      if(child.type === 'Group'){
        // Check if this group has LatheGeometry children (wheels)
        let hasWheel = false;
        for(let sub of child.children){
          if(sub.type === 'Mesh' && sub.geometry && sub.geometry.type === 'LatheGeometry'){
            hasWheel = true;
            break;
          }
        }
        if(hasWheel){
          child.rotation.x += delta * 0.5;
        }
        findAndRotateWheels(child);
      }
    }
  }
  
  findAndRotateWheels(scene);
  
  // Zoom wheel rotation
  zoomWheel.rotation.z += delta * 0.6;
  
  // Zoom wheel subtle bounce/pulse for realism
  const bounce = 0.001 * Math.sin(elapsed * 0.5);
  zoomWheel.position.y = 0.02 + bounce;
  
  // Gantry status light pulse
  for(let child of gantry.children){
    if(child.type === 'Mesh' && child.geometry && child.geometry.type === 'SphereGeometry'){
      child.material.emissiveIntensity = 0.3 + 0.4 * Math.sin(elapsed * 2);
    }
  }
  
  // Defect markers animation
  defectAnimPhase += delta;
  for(let i = 0; i < defectMarkers.length; i++){
    const dm = defectMarkers[i];
    const phase = defectAnimPhase + i * 0.5;
    const zPos = Math.sin(phase * 0.5) * 0.5;
    dm.visible = scanActive && Math.abs(zPos) < 0.3;
    if(dm.visible){
      dm.position.z = scanPos + zPos;
      dm.position.y = 0.35 + 0.1 * Math.sin(phase * 3);
      const pulse = 0.5 + 0.5 * Math.sin(phase * 5);
      dm.material.emissiveIntensity = pulse * 0.8;
    }
  }
  
  // Update controls
  controls.update();
  
  // Render main scene
  renderer.render(scene, camera);
  
  // Render zoom scene
  const zoomPulse = 0.05 * Math.sin(elapsed * 0.5);
  zoomCamera.position.x = 0.8 + zoomPulse * 0.3;
  zoomCamera.position.y = 0.4 + 0.1 * Math.sin(elapsed * 0.3);
  zoomCamera.lookAt(0, 0.05, 0);
  zoomRenderer.render(zoomScene, zoomCamera);
  
  requestAnimationFrame(animate);
}

animate();

// ======================================================================
// RESIZE HANDLER
// ======================================================================
function handleResize(){
  const mainW = container.clientWidth;
  const mainH = container.clientHeight;
  camera.aspect = mainW / mainH;
  camera.updateProjectionMatrix();
  renderer.setSize(mainW, mainH);
  
  const zw = zoomContainer.clientWidth;
  const zh = zoomContainer.clientHeight;
  if(zw > 0 && zh > 0){
    zoomCamera.aspect = zw / zh;
    zoomCamera.updateProjectionMatrix();
    zoomRenderer.setSize(zw, zh);
  }
}
window.addEventListener('resize', handleResize);

// ======================================================================
// ANALYTICS
// ======================================================================
const trackData = {p: window.location.pathname, r: document.referrer, t: navigator.userAgent};
navigator.sendBeacon('/api/track', JSON.stringify(trackData));
fetch('/api/track', {method:'POST', body:JSON.stringify(trackData), headers:{'Content-Type':'application/json'}}).catch(()=>{});

// ======================================================================
// CLICK TO TOGGLE AUTO-ROTATION
// ======================================================================
renderer.domElement.addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate;
  const status = document.getElementById('scan-status');
  if(!controls.autoRotate){
    status.textContent = '⏸ 视角已暂停 · 点击恢复';
    status.classList.add('active');
  } else {
    status.textContent = '⚡ 激光扫描检测中 ...';
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