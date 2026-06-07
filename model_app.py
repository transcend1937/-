"""
万象归踪 — 3D交互模型展示网站
基于Three.js构建的轮对检测+碳减排过程3D模拟
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>万象归踪 · 3D模拟演示</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;overflow:hidden;background:#0a0e1a;color:#fff}
#canvas-container{width:100vw;height:100vh;display:block}

/* HUD overlay */
#hud{position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:10}
#title-bar{position:absolute;top:24px;left:50%;transform:translateX(-50%);text-align:center;
  background:rgba(10,14,26,0.75);backdrop-filter:blur(16px);padding:14px 36px;
  border-radius:16px;border:1px solid rgba(255,255,255,0.08);pointer-events:auto}
#title-bar h1{font-size:22px;font-weight:700;background:linear-gradient(135deg,#5eead4,#2dd4bf,#06b6d4);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
#title-bar .sub{font-size:13px;color:rgba(255,255,255,0.5);margin-top:4px}
#title-bar .sub span{background:rgba(45,212,191,0.15);color:#5eead4;padding:2px 10px;border-radius:6px}

/* Data dashboard */
#dashboard{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);
  display:flex;gap:16px;pointer-events:auto;flex-wrap:wrap;justify-content:center}
.d-card{background:rgba(10,14,26,0.8);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.06);
  border-radius:14px;padding:14px 22px;min-width:130px;text-align:center;
  transition:all 0.3s ease}
.d-card:hover{transform:translateY(-4px);border-color:rgba(45,212,191,0.3)}
.d-card .num{font-size:28px;font-weight:700;line-height:1.2}
.d-card .label{font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px}
.c-green .num{color:#5eead4}
.c-blue .num{color:#38bdf8}
.c-purple .num{color:#a78bfa}
.c-amber .num{color:#fbbf24}

/* Control hint */
#hint{position:absolute;bottom:100px;left:50%;transform:translateX(-50%);
  font-size:12px;color:rgba(255,255,255,0.25);text-align:center;pointer-events:none;
  background:rgba(0,0,0,0.4);padding:8px 20px;border-radius:20px;backdrop-filter:blur(4px)}

/* Status badge */
#status-badge{position:absolute;top:24px;right:24px;pointer-events:auto}
#status-badge .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;animation:pulse 1.5s infinite}
#status-badge .dot.green{background:#5eead4;box-shadow:0 0 12px rgba(94,234,212,0.5)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
#status-badge span{font-size:12px;color:rgba(255,255,255,0.5)}

/* Phase indicator */
#phase{position:absolute;top:90px;left:50%;transform:translateX(-50%);pointer-events:none;
  font-size:14px;color:rgba(255,255,255,0.6);background:rgba(10,14,26,0.6);backdrop-filter:blur(8px);
  padding:8px 24px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);opacity:0;transition:opacity 0.5s}
#phase.show{opacity:1}

/* Legend */
#legend{position:absolute;bottom:110px;right:24px;pointer-events:none;
  background:rgba(10,14,26,0.7);backdrop-filter:blur(8px);padding:12px 16px;border-radius:10px;
  border:1px solid rgba(255,255,255,0.06);font-size:12px;line-height:1.8}
#legend .row{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,0.5)}
#legend .color-box{width:14px;height:14px;border-radius:4px}

@media(max-width:768px){
  #title-bar{top:12px;padding:10px 18px;width:90%}
  #title-bar h1{font-size:17px}
  #dashboard{bottom:16px;gap:8px}
  .d-card{padding:10px 14px;min-width:90px}
  .d-card .num{font-size:20px}
  #legend{display:none}
  #hint{bottom:80px;font-size:10px;padding:6px 14px}
  #phase{top:78px;font-size:12px;padding:6px 16px}
}
</style>
</head>
<body>

<div id="canvas-container"></div>

<div id="hud">
  <div id="title-bar">
    <h1>🚂 万象归踪 · 3D模拟</h1>
    <div class="sub"><span>🌱 智能检测驱动低碳运维</span> &nbsp; 轨边双向阵列成像系统</div>
  </div>

  <div id="status-badge"><span class="dot green"></span><span>系统运行中</span></div>

  <div id="phase">🔍 开始检测...</div>

  <div id="dashboard">
    <div class="d-card c-green"><div class="num" id="d-co2">0</div><div class="label">碳减排 (kgCO₂/次)</div></div>
    <div class="d-card c-blue"><div class="num" id="d-eff">0</div><div class="label">检测效率提升</div></div>
    <div class="d-card c-purple"><div class="num" id="d-def">0</div><div class="label">缺陷识别率</div></div>
    <div class="d-card c-amber"><div class="num" id="d-scan">0</div><div class="label">累计扫描 (次)</div></div>
  </div>

  <div id="hint">🖱 拖拽旋转 · 滚轮缩放</div>

  <div id="legend">
    <div class="row"><span class="color-box" style="background:#5eead4"></span> 检测激光束</div>
    <div class="row"><span class="color-box" style="background:#f87171"></span> 识别缺陷区域</div>
    <div class="row"><span class="color-box" style="background:#38bdf8"></span> 轨边阵列相机</div>
  </div>
</div>

<script>
// ===== Three.js 场景 =====
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e1a);
scene.fog = new THREE.Fog(0x0a0e1a, 30, 60);

const camera = new THREE.PerspectiveCamera(40, window.innerWidth/window.innerHeight, 0.1, 100);
camera.position.set(14, 8, 16);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
container.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.8;
controls.target.set(0, 0.5, 0);
controls.maxPolarAngle = Math.PI / 2.2;
controls.minDistance = 6;
controls.maxDistance = 30;

// ===== 灯光 =====
const ambientLight = new THREE.AmbientLight(0x222244, 0.4);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0x5eead4, 0x0a0e1a, 0.6);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
dirLight.position.set(8, 15, 5);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x5eead4, 0.3);
fillLight.position.set(-5, 3, -8);
scene.add(fillLight);

// ===== 地面 =====
const groundGeo = new THREE.PlaneGeometry(30, 20);
const groundMat = new THREE.MeshStandardMaterial({
  color: 0x141829,
  roughness: 0.9,
  metalness: 0.1,
});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.15;
ground.receiveShadow = true;
scene.add(ground);

// Grid
const gridHelper = new THREE.GridHelper(30, 30, 0x1a2a4a, 0x1a2a4a);
gridHelper.position.y = -0.1;
scene.add(gridHelper);

// ===== 轨道 =====
function createRail(zOffset) {
  const group = new THREE.Group();
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x4a5568, metalness: 0.8, roughness: 0.3
  });
  const railGeo = new THREE.BoxGeometry(0.08, 0.12, 12);
  const rail1 = new THREE.Mesh(railGeo, railMat);
  rail1.position.set(-0.72, 0.06, 0);
  rail1.castShadow = true;
  group.add(rail1);
  const rail2 = new THREE.Mesh(railGeo, railMat);
  rail2.position.set(0.72, 0.06, 0);
  rail2.castShadow = true;
  group.add(rail2);

  // Sleepers
  const sleeperMat = new THREE.MeshStandardMaterial({
    color: 0x5a4a3a, roughness: 0.9
  });
  for (let i = -5.5; i <= 5.5; i += 0.8) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.06, 0.14), sleeperMat);
    s.position.set(0, 0, i);
    s.castShadow = true;
    group.add(s);
  }
  group.position.z = zOffset;
  return group;
}

scene.add(createRail(0));

// ===== 火车轮对 =====
function createWheel(x, z, hasDefect) {
  const group = new THREE.Group();

  // 车轮
  const wheelMat = new THREE.MeshStandardMaterial({
    color: 0x8a9ba8, metalness: 0.6, roughness: 0.4
  });
  const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.12, 32);
  const wheel = new THREE.Mesh(wheelGeo, wheelMat);
  wheel.rotation.x = Math.PI / 2;
  wheel.castShadow = true;
  group.add(wheel);

  // 轮缘
  const rimMat = new THREE.MeshStandardMaterial({
    color: 0x6a7b88, metalness: 0.7, roughness: 0.3
  });
  const rimGeo = new THREE.TorusGeometry(0.53, 0.04, 16, 32);
  const rim = new THREE.Mesh(rimGeo, rimMat);
  rim.rotation.x = Math.PI / 2;
  rim.position.z = 0.07;
  group.add(rim);
  const rim2 = rim.clone();
  rim2.position.z = -0.07;
  group.add(rim2);

  // 轮轴
  const axleMat = new THREE.MeshStandardMaterial({
    color: 0x3a4a58, metalness: 0.8, roughness: 0.2
  });
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.44, 12), axleMat);
  axle.rotation.x = Math.PI / 2;
  group.add(axle);

  // 辐条
  for (let i = 0; i < 6; i++) {
    const angle = (i / 6) * Math.PI * 2;
    const spoke = new THREE.Mesh(
      new THREE.BoxGeometry(0.03, 0.03, 0.38),
      new THREE.MeshStandardMaterial({color: 0x7a8b98, metalness: 0.5, roughness: 0.5})
    );
    spoke.position.set(Math.cos(angle)*0.25, Math.sin(angle)*0.25, 0);
    spoke.rotation.z = angle;
    group.add(spoke);
  }

  // 踏面缺陷标记
  if (hasDefect) {
    const defectMat = new THREE.MeshStandardMaterial({
      color: 0xf87171, emissive: 0xf87171, emissiveIntensity: 0.3
    });
    const defect = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), defectMat);
    defect.position.set(0, 0.45, 0);
    defect.name = 'defect';
    group.add(defect);
  }

  group.position.set(x, 0.25, z);
  return group;
}

// 轮对1 (带缺陷) - 在检测区
const wheelGroup1 = createWheel(0.2, 1.5, true);
scene.add(wheelGroup1);

// 轮对2 (无缺陷) - 在等待区
const wheelGroup2 = createWheel(-0.2, -2.2, false);
scene.add(wheelGroup2);

// 轮对3 (带缺陷) - 等待区
const wheelGroup3 = createWheel(0.2, -3.8, true);
scene.add(wheelGroup3);

// ===== 轨边阵列相机 =====
function createCameraArray(x, zOffset) {
  const group = new THREE.Group();
  const poleMat = new THREE.MeshStandardMaterial({color: 0x6a7b88, metalness: 0.7, roughness: 0.3});
  const camMat = new THREE.MeshStandardMaterial({color: 0x38bdf8, emissive: 0x38bdf8, emissiveIntensity: 0.15});

  for (let i = -2; i <= 2; i += 0.6) {
    // 支柱
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.5, 6), poleMat);
    pole.position.set(0, 0.25, i);
    group.add(pole);

    // 相机头
    const cam = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 0.1), camMat);
    cam.position.set(0.02, 0.55, i);
    cam.name = 'camera';
    group.add(cam);

    // 镜头光晕 (小发光球)
    const lensGlow = new THREE.Mesh(
      new THREE.SphereGeometry(0.025, 6, 6),
      new THREE.MeshBasicMaterial({color: 0x7dd3fc})
    );
    lensGlow.position.set(0.07, 0.55, i);
    lensGlow.name = 'lens';
    group.add(lensGlow);
  }

  group.position.set(x, 0, zOffset);
  return group;
}

// 左侧阵列
const leftArray = createCameraArray(-1.2, 0.8);
scene.add(leftArray);

// 右侧阵列
const rightArray = createCameraArray(1.2, 0.8);
scene.add(rightArray);

// ===== 检测激光束 =====
function createLaserBeam() {
  const group = new THREE.Group();

  // 主光束
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0x5eead4, transparent: true, opacity: 0.6
  });
  const beam = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.015, 2.4), beamMat);
  beam.name = 'mainBeam';
  group.add(beam);

  // 发光粒子效果
  const particles = new THREE.BufferGeometry();
  const positions = new Float32Array(30 * 3);
  for (let i = 0; i < 30; i++) {
    positions[i*3] = (Math.random() - 0.5) * 0.1;
    positions[i*3+1] = (Math.random() - 0.5) * 0.1;
    positions[i*3+2] = (Math.random() - 0.5) * 2.4;
  }
  particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const particleMat = new THREE.PointsMaterial({
    color: 0x5eead4, size: 0.015, transparent: true, opacity: 0.5
  });
  const particleSystem = new THREE.Points(particles, particleMat);
  particleSystem.name = 'particles';
  group.add(particleSystem);

  // 端点光晕
  const glowMat = new THREE.MeshBasicMaterial({
    color: 0x5eead4, transparent: true, opacity: 0.3
  });
  const glow = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), glowMat);
  glow.position.set(0, 0, 1.2);
  glow.name = 'endGlow';
  group.add(glow);

  group.position.set(0, 0.12, 0.5);
  return group;
}

const laserBeam = createLaserBeam();
scene.add(laserBeam);

// ===== 扫描线 (横移扫描) =====
const scanLineMat = new THREE.MeshBasicMaterial({
  color: 0x5eead4, transparent: true, opacity: 0.2
});
const scanLine = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.01, 1.0), scanLineMat);
scanLine.position.set(0, 0.3, 0);
scene.add(scanLine);

// ===== 环境光晕粒子 =====
const starGeo = new THREE.BufferGeometry();
const starCount = 400;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount*3; i++) {
  starPos[i] = (Math.random() - 0.5) * 60;
}
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starMat = new THREE.PointsMaterial({
  color: 0x5eead4, size: 0.04, transparent: true, opacity: 0.15
});
const stars = new THREE.Points(starGeo, starMat);
stars.position.y = 2;
scene.add(stars);

// ===== 动画状态 =====
let scanPos = -1.0;
let scanDir = 1;
let scanCount = 0;
let co2Saved = 0;
let phaseText = '';
let defectHighlight = false;

const dCo2 = document.getElementById('d-co2');
const dEff = document.getElementById('d-eff');
const dDef = document.getElementById('d-def');
const dScan = document.getElementById('d-scan');
const phaseEl = document.getElementById('phase');

// ===== 动画循环 =====
function animate() {
  requestAnimationFrame(animate);

  // 扫描动画
  scanPos += scanDir * 0.012;
  if (scanPos > 1.0) {
    scanPos = -1.0;
    scanCount++;
    co2Saved += 0.25;
    dScan.textContent = scanCount;

    // 缺陷闪烁提示
    if (scanCount % 3 === 0) {
      defectHighlight = true;
      phaseEl.textContent = '⚠️ 检测到轮对踏面缺陷！碳排预警！';
      phaseEl.className = 'show';
      setTimeout(() => {
        defectHighlight = false;
        phaseEl.textContent = `🔍 第 ${scanCount} 次轨边扫描完成`;
      }, 2000);
    } else {
      phaseEl.textContent = `🔍 第 ${scanCount} 次轨边扫描完成 | 轮对状态正常`;
      phaseEl.className = 'show';
    }
  }

  // 激光束动画
  laserBeam.children.forEach(child => {
    if (child.name === 'mainBeam') {
      child.scale.z = 0.8 + Math.sin(Date.now() * 0.005) * 0.2;
    }
    if (child.name === 'endGlow') {
      child.scale.setScalar(1 + Math.sin(Date.now() * 0.01) * 0.3);
      child.material.opacity = 0.2 + Math.sin(Date.now() * 0.008) * 0.15;
    }
    if (child.name === 'particles') {
      child.rotation.z += 0.02;
    }
  });

  // 扫描线横移
  scanLine.position.x = scanPos * 0.5;
  laserBeam.position.z = 0.5 + scanPos * 0.8;

  // 缺陷高亮闪烁
  const defects = [];
  wheelGroup1.children.forEach(c => { if (c.name === 'defect') defects.push(c); });
  wheelGroup3.children.forEach(c => { if (c.name === 'defect') defects.push(c); });
  defects.forEach(d => {
    if (defectHighlight) {
      d.material.emissiveIntensity = 1.0;
      d.scale.setScalar(1 + Math.sin(Date.now() * 0.02) * 0.3);
    } else {
      d.material.emissiveIntensity = 0.2;
      d.scale.setScalar(1);
    }
  });

  // 轮对缓慢旋转
  wheelGroup1.children.forEach(c => {
    if (c.type === 'Mesh' && !c.name) { c.rotation.y += 0.01; }
  });
  wheelGroup2.children.forEach(c => {
    if (c.type === 'Mesh' && !c.name) { c.rotation.y += 0.01; }
  });

  // 相机阵列闪烁
  const camBlink = 0.15 + Math.sin(Date.now() * 0.003) * 0.08;
  scene.children.forEach(c => {
    if (c.type === 'Group') {
      c.children.forEach(ch => {
        if (ch.name === 'camera' || ch.name === 'lens') {
          ch.material && (ch.material.emissiveIntensity = camBlink);
        }
      });
    }
  });

  // 更新HUD数据
  const effVal = Math.min(5 + (co2Saved / 0.25) * 0.15, 15);
  dEff.textContent = effVal.toFixed(1) + 'x';
  dCo2.textContent = co2Saved.toFixed(1);
  dDef.textContent = Math.min(90 + (co2Saved / 0.25) * 0.3, 97.5).toFixed(1) + '%';

  controls.update();
  renderer.render(scene, camera);
}

animate();

// ===== 窗口自适应 =====
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// 点击/触摸时停止自动旋转
renderer.domElement.addEventListener('click', () => {
  controls.autoRotate = false;
  setTimeout(() => { controls.autoRotate = true; }, 8000);
});
renderer.domElement.addEventListener('touchstart', () => {
  controls.autoRotate = false;
  setTimeout(() => { controls.autoRotate = true; }, 8000);
});

// 初始化提示
setTimeout(() => {
  phaseEl.textContent = '🔍 轨边阵列相机启动，开始轮对踏面扫描...';
  phaseEl.className = 'show';
}, 500);

console.log('🚂 万象归踪 3D模拟已启动');
</script>
</body>
</html>"""

@app.get("/")
async def index():
    return HTMLResponse(HTML)

@app.get("/api/health")
async def health():
    return {"status": "ok", "project": "万象归踪·3D模拟"}