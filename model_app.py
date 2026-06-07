"""
万象归踪 — 3D交互模型展示网站
参照参考图：轮对平行排列在地面轨槽中，直线纵深排列
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
#legend{position:absolute;bottom:80px;right:20px;pointer-events:none;
  background:rgba(26,26,46,0.8);backdrop-filter:blur(8px);padding:10px 14px;border-radius:10px;
  border:1px solid rgba(255,255,255,0.06);font-size:11px;line-height:1.8}
#legend .row{display:flex;align-items:center;gap:6px;color:rgba(255,255,255,0.5)}
#legend .color-box{width:12px;height:12px;border-radius:3px}

/* Data footer */
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
    <div class="sub">参照检修车间轮对存放布局 · 轨槽平行排列</div>
  </div>

  <div id="legend">
    <div class="row"><span class="color-box" style="background:#60a5fa"></span> 标准轮对</div>
    <div class="row"><span class="color-box" style="background:#f87171"></span> 缺陷标记轮对</div>
    <div class="row"><span class="color-box" style="background:#34d399"></span> 检测完成</div>
  </div>

  <div id="data-bar">
    <div class="data-item"><div class="num" id="d-total">5</div><div class="label">轮对总数</div></div>
    <div class="data-item"><div class="num" id="d-defect">1</div><div class="label">缺陷轮对</div></div>
    <div class="data-item"><div class="num" id="d-pass">4</div><div class="label">检测通过</div></div>
  </div>

  <div id="hint">🖱 拖拽旋转 · 滚轮缩放 · 点击暂停自动旋转</div>
</div>

<script>
// ===== Three.js 场景 =====
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);
scene.fog = new THREE.Fog(0x1a1a2e, 18, 40);

// 侧视角：像参考图一样正面看到轮对侧面
const camera = new THREE.PerspectiveCamera(35, window.innerWidth/window.innerHeight, 0.1, 100);
camera.position.set(0, 4.5, 12);
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
controls.autoRotateSpeed = 0.5;
controls.target.set(0, 0.3, 0);
controls.maxPolarAngle = Math.PI / 2.5;
controls.minDistance = 4;
controls.maxDistance = 25;

// ===== 灯光 =====
const ambientLight = new THREE.AmbientLight(0x222244, 0.5);
scene.add(ambientLight);

const hemiLight = new THREE.HemisphereLight(0x60a5fa, 0x1a1a2e, 0.5);
scene.add(hemiLight);

const dirLight = new THREE.DirectionalLight(0xffeedd, 1.0);
dirLight.position.set(6, 12, 4);
dirLight.castShadow = true;
dirLight.shadow.mapSize.width = 2048;
dirLight.shadow.mapSize.height = 2048;
scene.add(dirLight);

const fillLight = new THREE.DirectionalLight(0x60a5fa, 0.3);
fillLight.position.set(-4, 2, -6);
scene.add(fillLight);

// 顶光 - 模拟车间灯光
const topLight = new THREE.DirectionalLight(0xffffff, 0.4);
topLight.position.set(0, 10, 0);
scene.add(topLight);

// ===== 地面 =====
const groundGeo = new THREE.PlaneGeometry(30, 30);
const groundMat = new THREE.MeshStandardMaterial({
  color: 0x2a2a3e,
  roughness: 0.9,
  metalness: 0.05,
});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.1;
ground.receiveShadow = true;
scene.add(ground);

// 轨槽 (地面凹槽)
const grooveMat = new THREE.MeshStandardMaterial({
  color: 0x1a1a2e,
  roughness: 1.0,
});
for (let z = -6; z <= 6; z += 0.08) {
  const groove = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.01, 0.04), grooveMat);
  groove.position.set(0, -0.09, z);
  scene.add(groove);
}

// 网格参考线
const gridHelper = new THREE.GridHelper(20, 20, 0x3a3a5e, 0x2a2a4e);
gridHelper.position.y = -0.08;
scene.add(gridHelper);

// ===== 轨道 (钢轨) =====
function createTrack() {
  const group = new THREE.Group();
  const railMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a, metalness: 0.8, roughness: 0.3
  });
  // 两条钢轨
  for (let side of [-1, 1]) {
    // 轨头
    const headGeo = new THREE.BoxGeometry(0.06, 0.04, 14);
    const head = new THREE.Mesh(headGeo, railMat);
    head.position.set(side * 0.72, 0.08, 0);
    head.castShadow = true;
    group.add(head);
    // 轨腰
    const webGeo = new THREE.BoxGeometry(0.04, 0.08, 14);
    const web = new THREE.Mesh(webGeo, railMat);
    web.position.set(side * 0.72, 0.02, 0);
    group.add(web);
    // 轨底
    const baseGeo = new THREE.BoxGeometry(0.1, 0.02, 14);
    const base = new THREE.Mesh(baseGeo, railMat);
    base.position.set(side * 0.72, -0.04, 0);
    group.add(base);
  }
  // 轨枕
  const sleeperMat = new THREE.MeshStandardMaterial({
    color: 0x6a5a4a, roughness: 0.9
  });
  for (let z = -6.5; z <= 6.5; z += 0.7) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.12), sleeperMat);
    s.position.set(0, -0.07, z);
    s.castShadow = true;
    group.add(s);
  }
  return group;
}
scene.add(createTrack());

// ===== 车轮组 =====
const WHEEL_RADIUS = 0.48;
const WHEEL_THICK = 0.12;
const AXLE_LEN = 1.44;
const AXLE_RADIUS = 0.08;

// 所有轮对组
const wheelsets = [];

function createWheelset(zPos, index) {
  const group = new THREE.Group();

  // 轮对材质
  const wheelMat = new THREE.MeshStandardMaterial({
    color: 0x7a8b9a,
    metalness: 0.7,
    roughness: 0.3,
  });
  const rimMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a,
    metalness: 0.8,
    roughness: 0.25,
  });
  const axleMat = new THREE.MeshStandardMaterial({
    color: 0x3a4a5a,
    metalness: 0.85,
    roughness: 0.2,
  });
  const hubMat = new THREE.MeshStandardMaterial({
    color: 0x6a7a8a,
    metalness: 0.6,
    roughness: 0.35,
  });

  // 左侧车轮
  const wheelL = new THREE.Mesh(new THREE.CylinderGeometry(WHEEL_RADIUS, WHEEL_RADIUS, WHEEL_THICK, 32), wheelMat);
  wheelL.rotation.x = Math.PI / 2;
  wheelL.position.x = -AXLE_LEN/2;
  wheelL.castShadow = true;
  group.add(wheelL);

  // 左轮轮缘
  const rimL = new THREE.Mesh(new THREE.TorusGeometry(WHEEL_RADIUS + 0.03, 0.035, 12, 32), rimMat);
  rimL.rotation.x = Math.PI / 2;
  rimL.position.set(-AXLE_LEN/2, 0, WHEEL_THICK/2 + 0.01);
  group.add(rimL);
  const rimL2 = rimL.clone();
  rimL2.position.z = -(WHEEL_THICK/2 + 0.01);
  group.add(rimL2);

  // 右侧车轮
  const wheelR = new THREE.Mesh(new THREE.CylinderGeometry(WHEEL_RADIUS, WHEEL_RADIUS, WHEEL_THICK, 32), wheelMat);
  wheelR.rotation.x = Math.PI / 2;
  wheelR.position.x = AXLE_LEN/2;
  wheelR.castShadow = true;
  group.add(wheelR);

  // 右轮轮缘
  const rimR = new THREE.Mesh(new THREE.TorusGeometry(WHEEL_RADIUS + 0.03, 0.035, 12, 32), rimMat);
  rimR.rotation.x = Math.PI / 2;
  rimR.position.set(AXLE_LEN/2, 0, WHEEL_THICK/2 + 0.01);
  group.add(rimR);
  const rimR2 = rimR.clone();
  rimR2.position.z = -(WHEEL_THICK/2 + 0.01);
  group.add(rimR2);

  // 轮轴
  const axle = new THREE.Mesh(new THREE.CylinderGeometry(AXLE_RADIUS, AXLE_RADIUS, AXLE_LEN, 12), axleMat);
  axle.rotation.x = Math.PI / 2;
  group.add(axle);

  // 轴端 (两侧凸台)
  for (let side of [-1, 1]) {
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.12, 0.14, 0.05, 12),
      hubMat
    );
    hub.rotation.x = Math.PI / 2;
    hub.position.x = side * (AXLE_LEN/2 + 0.025);
    group.add(hub);
  }

  // 辐板 (薄圆盘连接轮缘和轮毂)
  const webMat = new THREE.MeshStandardMaterial({
    color: 0x6a7a88,
    metalness: 0.5,
    roughness: 0.5,
  });
  for (let side of [-1, 1]) {
    // 辐板是连接车轮背面到车轴的薄盘
    const web = new THREE.Mesh(
      new THREE.RingGeometry(0.12, WHEEL_RADIUS - 0.04, 24),
      webMat
    );
    web.rotation.y = Math.PI / 2;
    web.rotation.x = Math.PI / 2;
    web.position.set(side * AXLE_LEN/2, 0, 0);
    group.add(web);
  }

  // 减速齿轮 (中间某组轮对带齿轮)
  if (index === 4) {
    const gearMat = new THREE.MeshStandardMaterial({
      color: 0x4a5a6a, metalness: 0.85, roughness: 0.2
    });
    const gear = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.08, 16),
      gearMat
    );
    gear.rotation.x = Math.PI / 2;
    gear.position.set(0, 0, 0.05);
    group.add(gear);
    // 齿轮齿
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const tooth = new THREE.Mesh(
        new THREE.BoxGeometry(0.04, 0.03, 0.06),
        gearMat
      );
      tooth.position.set(Math.cos(angle) * 0.2, Math.sin(angle) * 0.2, 0.05);
      tooth.rotation.z = angle;
      group.add(tooth);
    }
  }

  // 缺陷标记 (第2组轮对)
  if (index === 2) {
    const defMat = new THREE.MeshStandardMaterial({
      color: 0xf87171, emissive: 0xf87171, emissiveIntensity: 0.3
    });
    // 左轮踏面缺陷
    const def1 = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), defMat);
    def1.position.set(-AXLE_LEN/2, WHEEL_RADIUS - 0.02, WHEEL_THICK/2 + 0.02);
    def1.name = 'defect';
    group.add(def1);
    // 缺陷标记光圈
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xf87171, transparent: true, opacity: 0.3, side: THREE.DoubleSide
    });
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.06, 0.08, 16), ringMat);
    ring.position.copy(def1.position);
    ring.position.y += 0.01;
    ring.rotation.x = -Math.PI / 2;
    ring.name = 'defectRing';
    group.add(ring);
  }

  // 检测完成标记 (第5组轮对)
  if (index === 5) {
    const checkMat = new THREE.MeshBasicMaterial({
      color: 0x34d399, transparent: true, opacity: 0.2
    });
    const ring = new THREE.Mesh(new THREE.RingGeometry(WHEEL_RADIUS - 0.02, WHEEL_RADIUS, 32), checkMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.set(0, 0, 0);
    ring.name = 'checkRing';
    group.add(ring);
  }

  group.position.set(0, WHEEL_RADIUS, zPos);
  group.name = 'wheelset';
  return group;
}

// 排列5组轮对 - 沿Z轴直线排列，与参考图一致
const SPACING = 2.0;
for (let i = 0; i < 6; i++) {
  const z = (i - 2.5) * SPACING;
  const ws = createWheelset(z, i + 1);
  scene.add(ws);
  wheelsets.push(ws);
}

// ===== 车间背景设施 =====

// 两侧货架/支柱
const pillarMat = new THREE.MeshStandardMaterial({
  color: 0x3a4a5a, metalness: 0.6, roughness: 0.5
});
for (let side of [-1, 1]) {
  for (let z = -5; z <= 5; z += 2.5) {
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.8, 0.1), pillarMat);
    pillar.position.set(side * 2.0, 0.4, z);
    pillar.castShadow = true;
    scene.add(pillar);
  }
}

// 横梁 (连接两侧支柱)
const beamMat = new THREE.MeshStandardMaterial({
  color: 0x4a5a6a, metalness: 0.5, roughness: 0.6
});
for (let z = -5; z <= 5; z += 2.5) {
  const beam = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.06, 0.08), beamMat);
  beam.position.set(0, 0.85, z);
  scene.add(beam);
}

// 顶棚灯光
const lightMat = new THREE.MeshBasicMaterial({
  color: 0xffffee, transparent: true, opacity: 0.08
});
for (let z = -4; z <= 4; z += 2) {
  const lightStrip = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.02, 0.15), lightMat);
  lightStrip.position.set(0, 0.9, z);
  scene.add(lightStrip);
}

// ===== 轨边检测设备 (只在第一组轮对附近) =====
function createInspectionUnit() {
  const group = new THREE.Group();
  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x5a6a7a, metalness: 0.7, roughness: 0.3
  });
  const sensorMat = new THREE.MeshStandardMaterial({
    color: 0x60a5fa, emissive: 0x60a5fa, emissiveIntensity: 0.1
  });

  // 检测立柱 (轨边)
  for (let side of [-1, 1]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.6, 0.06), frameMat);
    post.position.set(side * 1.1, 0.3, 0);
    group.add(post);

    // 传感器头
    const sensor = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.08, 0.08), sensorMat);
    sensor.position.set(side * 1.16, 0.52, 0);
    sensor.name = 'sensor';
    group.add(sensor);

    // 传感器红光
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.02, 6, 6),
      new THREE.MeshBasicMaterial({color: 0xef4444})
    );
    glow.position.set(side * 1.22, 0.52, 0);
    glow.name = 'sensorGlow';
    group.add(glow);
  }

  // 横跨轨道的检测梁
  const crossBeam = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 2.4), frameMat);
  crossBeam.position.set(0, 0.62, 0);
  group.add(crossBeam);

  group.position.set(0, WHEEL_RADIUS, -SPACING * 1.5);
  return group;
}
scene.add(createInspectionUnit());

// ===== 背景粒子 =====
const starGeo = new THREE.BufferGeometry();
const starCount = 200;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount*3; i++) {
  starPos[i] = (Math.random() - 0.5) * 50;
}
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starMat = new THREE.PointsMaterial({
  color: 0x60a5fa, size: 0.03, transparent: true, opacity: 0.1
});
const stars = new THREE.Points(starGeo, starMat);
stars.position.y = 3;
scene.add(stars);

// ===== 动画 =====
let scanPhase = 0;
const dTotal = document.getElementById('d-total');
const dDefect = document.getElementById('d-defect');
const dPass = document.getElementById('d-pass');

function animate() {
  requestAnimationFrame(animate);

  const delta = 0.016; // ~60fps
  scanPhase += delta;

  // 轮对旋转 - 所有轮子缓慢旋转
  scene.children.forEach(obj => {
    if (obj.type === 'Group' && obj.name === 'wheelset') {
      // 只旋转轮子和轴（不是整个组里的标记物）
      obj.children.forEach(child => {
        // 轮子是CylinderGeometry Mesh，标记物有name属性
        if (child.type === 'Mesh' && !child.name && child.geometry) {
          child.rotation.y += 0.015;
        }
        // 轮缘(TorusGeometry)也要转
        if (child.type === 'Mesh' && child.geometry && child.geometry.type === 'TorusGeometry') {
          child.rotation.y += 0.015;
        }
      });
    }
  });

  // 传感器闪烁
  const blink = 0.08 + Math.sin(Date.now() * 0.004) * 0.06;
  scene.children.forEach(obj => {
    if (obj.type === 'Group') {
      obj.children.forEach(ch => {
        if (ch.name === 'sensor') {
          ch.material.emissiveIntensity = blink;
        }
        if (ch.name === 'sensorGlow') {
          ch.material.opacity = 0.3 + Math.sin(Date.now() * 0.005) * 0.3;
        }
        if (ch.name === 'checkRing') {
          ch.material.opacity = 0.15 + Math.sin(Date.now() * 0.003) * 0.1;
        }
        if (ch.name === 'defectRing') {
          ch.material.opacity = 0.2 + Math.sin(Date.now() * 0.008) * 0.15;
          ch.scale.setScalar(1 + Math.sin(Date.now() * 0.005) * 0.15);
        }
        if (ch.name === 'defect') {
          ch.material.emissiveIntensity = 0.2 + Math.sin(Date.now() * 0.006) * 0.2;
        }
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

// 点击暂停自动旋转
renderer.domElement.addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate;
});
renderer.domElement.addEventListener('touchstart', () => {
  controls.autoRotate = !controls.autoRotate;
});

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