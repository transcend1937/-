"""
万象归踪 — 3D交互模型展示网站
参照参考图：轮对平行排列在轨道上，中间由车轴相连
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>万象归踪 · 轮对排列展示</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PingFang SC','Microsoft YaHei',sans-serif;overflow:hidden;background:#1a1a2e;color:#fff}
#canvas-container{width:100vw;height:100vh;display:block}

/* HUD */
#hud{position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:10}
#title-bar{position:absolute;top:20px;left:50%;transform:translateX(-50%);text-align:center;
  background:rgba(26,26,46,0.85);backdrop-filter:blur(16px);padding:12px 30px;
  border-radius:14px;border:1px solid rgba(255,255,255,0.08);pointer-events:auto}
#title-bar h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,#60a5fa,#818cf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
#title-bar .sub{font-size:12px;color:rgba(255,255,255,0.45);margin-top:3px}

#hint{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);
  font-size:12px;color:rgba(255,255,255,0.25);text-align:center;
  background:rgba(0,0,0,0.4);padding:6px 18px;border-radius:20px}

/* Legend */
#legend{position:absolute;top:100px;left:20px;pointer-events:none;
  background:rgba(26,26,46,0.8);backdrop-filter:blur(8px);padding:10px 14px;border-radius:10px;
  border:1px solid rgba(255,255,255,0.06);font-size:11px;line-height:1.8}
#legend .row{display:flex;align-items:center;gap:6px;color:rgba(255,255,255,0.5)}
#legend .color-box{width:12px;height:12px;border-radius:3px}

#data-bar{position:absolute;bottom:60px;left:50%;transform:translateX(-50%);
  display:flex;gap:12px;pointer-events:auto}
.data-item{background:rgba(26,26,46,0.8);backdrop-filter:blur(12px);
  border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:8px 16px;text-align:center}
.data-item .num{font-size:20px;font-weight:700;color:#60a5fa}
.data-item .label{font-size:11px;color:rgba(255,255,255,0.4);margin-top:2px}

@media(max-width:768px){
  #title-bar{top:10px;padding:8px 16px;width:92%}
  #title-bar h1{font-size:16px}
  #data-bar{bottom:50px;gap:6px;flex-wrap:wrap;justify-content:center}
  .data-item{padding:6px 10px}
  .data-item .num{font-size:16px}
  #legend{display:none}
}
</style>
</head>
<body>

<div id="canvas-container"></div>

<div id="hud">
  <div id="title-bar">
    <h1>🚂 万象归踪 · 轮对排列</h1>
    <div class="sub">参照检修车间 · 轮对沿轨道平行排列 · 车轴居中相连</div>
  </div>

  <div id="legend">
    <div class="row"><span class="color-box" style="background:#8a9bb0"></span> 标准轮对</div>
    <div class="row"><span class="color-box" style="background:#f87171"></span> 缺陷标记</div>
    <div class="row"><span class="color-box" style="background:#34d399"></span> 检测完成</div>
  </div>

  <div id="data-bar">
    <div class="data-item"><div class="num" id="d-total">6</div><div class="label">轮对总数</div></div>
    <div class="data-item"><div class="num" id="d-defect">1</div><div class="label">缺陷轮对</div></div>
    <div class="data-item"><div class="num" id="d-pass">5</div><div class="label">检测通过</div></div>
  </div>

  <div id="hint">🖱 拖拽旋转 · 滚轮缩放 · 点击暂停自动旋转</div>
</div>

<script>
// ===== Three.js 场景 =====
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);
scene.fog = new THREE.Fog(0x1a1a2e, 20, 45);

// 侧视角：像参考图一样看到轮对侧面+车轴
const camera = new THREE.PerspectiveCamera(30, window.innerWidth/window.innerHeight, 0.1, 100);
camera.position.set(5, 3, 5);
camera.lookAt(0, 0.3, 0);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
container.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.8;
controls.target.set(0, 0.3, 0);
controls.maxPolarAngle = Math.PI / 2.2;
controls.minDistance = 3;
controls.maxDistance = 25;

// ===== 灯光 =====
const ambientLight = new THREE.AmbientLight(0x222244, 0.6);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0x60a5fa, 0x1a1a2e, 0.6);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffeedd, 1.2);
dirLight.position.set(6, 12, 4);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x60a5fa, 0.3);
fillLight.position.set(-4, 2, -6);
scene.add(fillLight);

// ===== 地面 =====
const groundGeo = new THREE.PlaneGeometry(30, 30);
const groundMat = new THREE.MeshStandardMaterial({
  color: 0x2a2a3e, roughness: 0.9, metalness: 0.05
});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.1;
ground.receiveShadow = true;
scene.add(ground);

// 网格
const gridHelper = new THREE.GridHelper(20, 20, 0x3a3a5e, 0x2a2a4e);
gridHelper.position.y = -0.08;
scene.add(gridHelper);

// ===== 轨道 =====
function createTrack() {
  const group = new THREE.Group();
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a, metalness: 0.8, roughness: 0.3
  });
  for (let side of [-1, 1]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.08, 16), railMat);
    rail.position.set(side * 0.72, 0.06, 0);
    rail.castShadow = true;
    group.add(rail);
  }
  const sleeperMat = new THREE.MeshStandardMaterial({
    color: 0x6a5a4a, roughness: 0.9
  });
  for (let z = -7; z <= 7; z += 0.7) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.05, 0.1), sleeperMat);
    s.position.set(0, -0.06, z);
    group.add(s);
  }
  return group;
}
scene.add(createTrack());

// ===== 车轮组 =====
// 沿用第一版方案：两个轮子平行轨道，中间车轴相连
const WHEEL_RADIUS = 0.48;
const WHEEL_THICK = 0.10;
const AXLE_LEN = 1.44;
const AXLE_RADIUS = 0.07;

// 真实车轮轮廓 - LatheGeometry 沿 Z 轴（轮子朝Z方向/平行轨道）
// 车轮剖面点 (半径, 高度) - 向左旋转使车轮面朝Z方向
const pts = [
  // 轮缘顶部 (最外)
  [WHEEL_RADIUS + 0.04, WHEEL_THICK/2 + 0.02],
  // 轮缘外侧
  [WHEEL_RADIUS + 0.02, WHEEL_THICK/2],
  // 轮缘根部
  [WHEEL_RADIUS, WHEEL_THICK/2 - 0.01],
  // 踏面 (锥度1:20)
  [WHEEL_RADIUS - 0.005, WHEEL_THICK/2 - 0.02],
  [WHEEL_RADIUS - 0.015, 0],
  // 内侧踏面
  [WHEEL_RADIUS - 0.005, -WHEEL_THICK/2 + 0.02],
  [WHEEL_RADIUS, -WHEEL_THICK/2 + 0.01],
  // 轮缘内侧
  [WHEEL_RADIUS + 0.02, -WHEEL_THICK/2],
  // 轮缘顶部
  [WHEEL_RADIUS + 0.04, -WHEEL_THICK/2 - 0.02],
];
// 转为Vector2
const profilePoints = pts.map(p => new THREE.Vector2(p[0], p[1]));

// 轮辐剖面点
const webPts = [
  [0.20, WHEEL_THICK/2 - 0.01],
  [WHEEL_RADIUS - 0.03, WHEEL_THICK/2 - 0.02],
  [WHEEL_RADIUS - 0.03, -WHEEL_THICK/2 + 0.02],
  [0.20, -WHEEL_THICK/2 + 0.01],
];
const webProfile = webPts.map(p => new THREE.Vector2(p[0], p[1]));

function createWheel(hasDefect, hasGear, hasPass) {
  const group = new THREE.Group();

  // 主材质
  const wheelMat = new THREE.MeshStandardMaterial({
    color: 0x7a8b9a, metalness: 0.7, roughness: 0.3
  });
  const rimMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a, metalness: 0.8, roughness: 0.25
  });
  const axleMat = new THREE.MeshStandardMaterial({
    color: 0x3a4a5a, metalness: 0.85, roughness: 0.2
  });
  const hubMat = new THREE.MeshStandardMaterial({
    color: 0x6a7a8a, metalness: 0.6, roughness: 0.35
  });

  // === 车轮主体 ===
  // 使用LatheGeometry生成真实轮型，绕Y轴旋转
  // 为让车轮面朝Z（平行轨道），将整个组绕X旋转-90°
  const wheel = new THREE.Mesh(
    new THREE.LatheGeometry(profilePoints, 36),
    wheelMat
  );
  wheel.castShadow = true;
  group.add(wheel);

  // 轮辐 (薄盘连接轮毂到踏面)
  const web = new THREE.Mesh(
    new THREE.LatheGeometry(webProfile, 24),
    wheelMat
  );
  group.add(web);

  // 轮毂 (中心凸台)
  const hub = new THREE.Mesh(
    new THREE.CylinderGeometry(0.15, 0.17, 0.06, 12),
    hubMat
  );
  hub.position.y = 0;
  group.add(hub);

  // 整个组绕X轴旋转-90°，让车轮面朝Z方向 (平行于轨道)
  // 原来的Y轴（轮轴）变成Z轴
  group.rotation.x = -Math.PI / 2;

  // 缺陷标记
  if (hasDefect) {
    const defMat = new THREE.MeshStandardMaterial({
      color: 0xf87171, emissive: 0xf87171, emissiveIntensity: 0.5
    });
    const def = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), defMat);
    def.position.set(WHEEL_RADIUS - 0.01, 0, 0.06);
    def.name = 'defect';
    group.add(def);
    // 光晕环
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0xf87171, transparent: true, opacity: 0.3
    });
    const glowRing = new THREE.Mesh(new THREE.RingGeometry(0.06, 0.1, 16), glowMat);
    glowRing.position.set(WHEEL_RADIUS - 0.01, 0, 0.065);
    glowRing.rotation.x = -Math.PI / 2;
    glowRing.name = 'defectGlow';
    group.add(glowRing);
  }

  return group;
}

function createWheelset(zPos, index) {
  const group = new THREE.Group();
  group.name = 'wheelset';

  // 两个车轮与轨道平行摆放，中间车轴相连
  // 车轮面朝Z方向（平行于轨道延伸方向）
  // 车轴沿X方向连接左右车轮

  // 左侧车轮 (位于 -AXLE_LEN/2)
  const leftWheel = createWheel(
    index === 2,    // 第2组有缺陷
    index === 4,    // 第4组有齿轮
    index === 5     // 第5组检测完成
  );
  leftWheel.position.x = -AXLE_LEN/2;
  group.add(leftWheel);

  // 右侧车轮
  const rightWheel = createWheel(
    index === 2,
    index === 4,
    index === 5
  );
  rightWheel.position.x = AXLE_LEN/2;
  group.add(rightWheel);

  // 车轴 (柱子) - 连接两个车轮的中间柱
  const axleMat = new THREE.MeshStandardMaterial({
    color: 0x3a4a5a, metalness: 0.85, roughness: 0.2
  });
  const axle = new THREE.Mesh(
    new THREE.CylinderGeometry(AXLE_RADIUS, AXLE_RADIUS, AXLE_LEN, 12),
    axleMat
  );
  axle.rotation.z = Math.PI / 2; // 沿X方向
  axle.name = 'axle';
  group.add(axle);

  // 轴端凸台 (两侧)
  const hubMat = new THREE.MeshStandardMaterial({
    color: 0x6a7a8a, metalness: 0.6, roughness: 0.35
  });
  for (let side of [-1, 1]) {
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.13, 0.15, 0.05, 12),
      hubMat
    );
    hub.rotation.z = Math.PI / 2;
    hub.position.x = side * (AXLE_LEN/2 + 0.025);
    group.add(hub);
  }

  // 齿轮 (第4组)
  if (index === 4) {
    const gearMat = new THREE.MeshStandardMaterial({
      color: 0x4a5a6a, metalness: 0.85, roughness: 0.2
    });
    const gear = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.08, 16),
      gearMat
    );
    gear.rotation.z = Math.PI / 2;
    gear.position.x = 0;
    group.add(gear);
    // 齿轮齿
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const tooth = new THREE.Mesh(
        new THREE.BoxGeometry(0.04, 0.03, 0.06),
        gearMat
      );
      tooth.position.set(0, Math.cos(angle) * 0.2, Math.sin(angle) * 0.2);
      tooth.name = 'gearTooth';
      group.add(tooth);
    }
  }

  // 检测通过光环 (第5组)
  if (index === 5) {
    const checkMat = new THREE.MeshBasicMaterial({
      color: 0x34d399, transparent: true, opacity: 0.15
    });
    const ring = new THREE.Mesh(new THREE.RingGeometry(WHEEL_RADIUS - 0.02, WHEEL_RADIUS + 0.02, 32), checkMat);
    ring.rotation.y = Math.PI / 2;
    ring.position.x = 0;
    ring.name = 'checkRing';
    group.add(ring);
  }

  group.position.set(0, WHEEL_RADIUS + 0.06, zPos);
  return group;
}

// 排列6组轮对 - 沿Z轴直线排列
const SPACING = 2.2;
for (let i = 0; i < 6; i++) {
  const z = (i - 2.5) * SPACING;
  const ws = createWheelset(z, i + 1);
  scene.add(ws);
}

// ===== 车间背景 =====
const pillarMat = new THREE.MeshStandardMaterial({
  color: 0x3a4a5a, metalness: 0.6, roughness: 0.5
});
for (let side of [-1, 1]) {
  for (let z = -5; z <= 5; z += 2.5) {
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 0.1), pillarMat);
    pillar.position.set(side * 2.2, 0.4, z);
    scene.add(pillar);
  }
}

const beamMat = new THREE.MeshStandardMaterial({
  color: 0x4a5a6a, metalness: 0.5, roughness: 0.6
});
for (let z = -5; z <= 5; z += 2.5) {
  const beam = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.06, 0.08), beamMat);
  beam.position.set(0, 0.85, z);
  scene.add(beam);
}

// 顶光
const lightMat = new THREE.MeshBasicMaterial({
  color: 0xffffee, transparent: true, opacity: 0.08
});
for (let z = -4; z <= 4; z += 2) {
  const strip = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.02, 0.15), lightMat);
  strip.position.set(0, 0.9, z);
  scene.add(strip);
}

// 轨边检测设备
function createInspectionUnit() {
  const group = new THREE.Group();
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a, metalness: 0.7, roughness: 0.3
  });
  const sensorMat = new THREE.MeshStandardMaterial({
    color: 0x60a5fa, emissive: 0x60a5fa, emissiveIntensity: 0.1
  });
  for (let side of [-1, 1]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.6, 0.06), frameMat);
    post.position.set(side * 1.1, 0.3, -2.5);
    group.add(post);
    const sensor = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.08, 0.08), sensorMat);
    sensor.position.set(side * 1.16, 0.52, -2.5);
    sensor.name = 'sensor';
    group.add(sensor);
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.02, 6, 6),
      new THREE.MeshBasicMaterial({color: 0xef4444})
    );
    glow.position.set(side * 1.22, 0.52, -2.5);
    glow.name = 'sensorGlow';
    group.add(glow);
  }
  return group;
}
scene.add(createInspectionUnit());

// ===== 动画 =====
function animate() {
  requestAnimationFrame(animate);

  // 轮对旋转 - 所有轮子绕车轴（X轴）旋转
  scene.children.forEach(obj => {
    if (obj.type === 'Group' && obj.name === 'wheelset') {
      // 旋转整个轮对组里的车轮（绕X轴 = 车轴方向）
      obj.children.forEach(child => {
        // 车轮组有 rotation.x = -PI/2，所以子对象的rotation.z会绕车轴转
        if (child.type === 'Group') {
          child.rotation.z += 0.02; // 绕车轴旋转
        }
        // 车轴本身不旋转（它是静止的柱子）
      });
    }
  });

  // 传感器闪烁
  const blink = 0.08 + Math.sin(Date.now() * 0.004) * 0.06;
  scene.children.forEach(obj => {
    if (obj.type === 'Group') {
      obj.children.forEach(ch => {
        if (ch.name === 'sensor') ch.material.emissiveIntensity = blink;
        if (ch.name === 'sensorGlow') ch.material.opacity = 0.3 + Math.sin(Date.now() * 0.005) * 0.3;
        if (ch.name === 'checkRing') ch.material.opacity = 0.15 + Math.sin(Date.now() * 0.003) * 0.1;
        if (ch.name === 'defectGlow') {
          ch.material.opacity = 0.2 + Math.sin(Date.now() * 0.008) * 0.15;
          ch.scale.setScalar(1 + Math.sin(Date.now() * 0.005) * 0.15);
        }
        if (ch.name === 'defect') ch.material.emissiveIntensity = 0.2 + Math.sin(Date.now() * 0.006) * 0.2;
      });
    }
  });

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

renderer.domElement.addEventListener('click', () => { controls.autoRotate = !controls.autoRotate; });
renderer.domElement.addEventListener('touchstart', () => { controls.autoRotate = !controls.autoRotate; });

console.log('🚂 万象归踪 · 轮对排列展示已启动');
</script>
</body>
</html>"""

@app.get("/")
async def index():
    return HTMLResponse(HTML)

@app.get("/api/health")
async def health():
    return {"status": "ok", "project": "万象归踪·轮对排列"}