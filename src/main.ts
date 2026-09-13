import './style.css';
import { icon } from './icons';
import { objects, type ObjectId, type Mode, type View } from './catalog';
import { StudioRoom } from './room';
import { AmbientAudio } from './audio';

const app = document.querySelector<HTMLDivElement>('#app')!;
app.innerHTML = `
  <header class="topbar">
    <button class="brand" id="brand" aria-label="WEER Studio กลับมุมเริ่มต้น"><span class="brand-mark">W<span>↗</span></span><span class="brand-name">WEER<span>STUDIO</span></span></button>
    <div class="topbar-center"><span class="little-line"></span> A ROOM OF POSSIBILITIES</div>
    <div class="topbar-actions"><span class="live-pill"><i></i> INTERACTIVE SPACE</span><button class="icon-button" id="help" aria-label="วิธีใช้งาน">${icon('help')}</button></div>
  </header>
  <main>
    <section class="page-heading">
      <div><div class="eyebrow">THE WORKSPACE COLLECTION <span>/ 01</span></div><h1>A space to make things<span>.</span></h1><p>ห้องทำงานเล็ก ๆ ที่คุณสำรวจและปรับบรรยากาศได้ด้วยตัวเอง</p></div>
      <div class="room-spec"><span>3.5 × 3.5 <small>m</small></span><div>COMPACT SPACE. BIG IDEAS.</div></div>
    </section>
    <section class="experience" aria-label="สำรวจห้องทำงาน">
      <div class="scene-panel">
        <div class="scene-top"><span class="scene-tag"><span class="status-dot"></span> THE STUDIO <span class="scene-number">01</span></span><div class="scene-actions"><button class="icon-button" id="labels" aria-label="ซ่อนจุดเลือกวัตถุ" aria-pressed="true">${icon('eye')}</button><button class="icon-button" id="settings" aria-label="ตั้งค่าการแสดงผล">${icon('settings')}</button><button class="icon-button" id="fullscreen" aria-label="ขยายเต็มหน้าจอ">${icon('expand')}</button></div></div>
        <div id="stage" class="scene-stage"><div id="hotspots" class="hotspots"></div></div>
        <div class="loading" id="loading" role="status"><div class="loading-symbol">${icon('cube')}</div><p>Opening your space<span>กำลังโหลดโมเดลห้องทำงาน</span></p><div class="progress-track"><div id="progress"></div></div><small id="progress-label">0%</small></div>
        <div class="scene-caption"><span class="caption-line"></span><span>Made for focus.<br><em>Designed for you.</em></span></div>
        <div id="mobile-selection" class="mobile-selection" hidden></div>
        <div class="scene-bottom"><div class="view-picker" aria-label="มุมมองกล้อง"><button data-view="overview" class="active" aria-pressed="true">${icon('cube')}<span>ภาพรวม</span></button><button data-view="desk" aria-pressed="false">${icon('monitor')}<span>มุมทำงาน</span></button><button data-view="lounge" aria-pressed="false">${icon('leaf')}<span>มุมพักผ่อน</span></button></div><div class="view-actions"><button class="icon-button" id="tour" aria-label="เริ่มชมรอบห้อง" aria-pressed="false">${icon('play')}</button><button class="icon-button" id="reset-camera" aria-label="รีเซ็ตมุมกล้อง">${icon('reset')}</button></div></div>
        <div class="canvas-hint">${icon('move')} ลากเพื่อหมุน <span>·</span> ${icon('zoom')} เลื่อนเพื่อซูม <span>·</span> คลิกเพื่อสำรวจ</div>
      </div>
      <aside class="sidebar" aria-label="แผงควบคุมห้อง">
        <div class="sidebar-intro"><div class="eyebrow">MAKE IT YOURS</div><h2>A little more you.</h2><p>เลือกวัตถุ แล้วลองทำให้ห้องมีชีวิต</p></div>
        <div class="atmosphere"><span>บรรยากาศ</span><div class="mode-picker" aria-label="บรรยากาศห้อง"><button id="day" class="active" aria-pressed="true">${icon('sun')}กลางวัน</button><button id="night" aria-pressed="false">${icon('moon')}กลางคืน</button></div></div>
        <div class="object-section"><div class="section-label">สำรวจวัตถุ <span>09 OBJECTS</span></div><div class="object-grid">${objects.map(o => `<button class="object-card" data-object="${o.id}" aria-pressed="false" disabled>${icon(o.icon)}<span>${o.title}</span><i></i></button>`).join('')}</div></div>
        <div id="details" class="details" aria-live="polite"><div class="empty-detail">${icon('cube')}<h3>Every object has a story.</h3><p>คลิกจุดบนโมเดล หรือเลือกวัตถุด้านบน<br>เพื่อทดลองใช้งานในแบบของคุณ</p><span class="mini-label">EXPLORE AT YOUR OWN PACE</span></div></div>
        <div class="sidebar-footer"><span class="status-dot"></span><span id="system-status" role="status">กำลังเตรียมห้องของคุณ</span><span class="tiny-arrow">↗</span></div>
      </aside>
    </section>
    <footer class="page-footer"><span>DESIGNED WITH INTENTION.</span><span>WEER STUDIO <span class="footer-separator">/</span> YOUR SPACE, YOUR RHYTHM.</span><button id="about">เกี่ยวกับห้องนี้ ${icon('arrow')}</button></footer>
  </main>
  <div class="tooltip" id="tooltip" role="tooltip" hidden></div>
  <div class="toast" id="toast" role="status" hidden></div>
  <dialog id="dialog" aria-labelledby="dialog-title"><button class="dialog-close icon-button" id="close-dialog" aria-label="ปิดหน้าต่าง">${icon('close')}</button><div id="dialog-content"></div></dialog>
`;

const $ = <T extends HTMLElement = HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const audio = new AmbientAudio();
let room: StudioRoom | undefined;
let toastTimer: ReturnType<typeof setTimeout>;
let busyAudio = false;
let shadows = true;
let highQuality = true;
let exposure = 1.05;
const toast = (message: string) => {
  const el = $('#toast'); el.textContent = message; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 3200);
};
const statusOf = (id: ObjectId) => {
  if (!room) return '';
  const s = room.state;
  switch (id) {
    case 'chair': return `${Math.round(s.chair * 180 / Math.PI) % 360}°`;
    case 'monitors': return ['งานออกแบบ', 'โหมดโฟกัส', 'ปิดหน้าจอ'][s.monitors];
    case 'lamp': return s.lamp ? 'เปิดอยู่' : 'ปิดอยู่';
    case 'logo': return s.logo ? 'เปิดอยู่' : 'ปิดอยู่';
    case 'door': return s.door ? 'เปิดอยู่' : 'ปิดอยู่';
    case 'drawers': return s.drawers[s.drawer] ? 'เปิดอยู่' : 'ปิดอยู่';
    case 'blinds': return s.blinds ? 'เปิดรับแสง' : 'ลดมู่ลี่';
    case 'ac': return s.ac ? `${s.temperature}°C · ทำงาน` : 'ปิดอยู่';
    case 'radio': return audio.playing ? 'กำลังเล่น' : 'ปิดเสียง';
  }
};
const actionOf = (id: ObjectId) => {
  if (!room) return '';
  const s = room.state;
  switch (id) {
    case 'lamp': return s.lamp ? 'ปิดโคมไฟ' : 'เปิดโคมไฟ';
    case 'logo': return s.logo ? 'ปิดไฟโลโก้' : 'เปิดไฟโลโก้';
    case 'door': return s.door ? 'ปิดประตู' : 'เปิดประตู';
    case 'drawers': return s.drawers[s.drawer] ? 'ปิดลิ้นชัก' : 'เปิดลิ้นชัก';
    case 'blinds': return s.blinds ? 'ลดมู่ลี่' : 'ยกมู่ลี่';
    case 'ac': return s.ac ? 'ปิดเครื่องปรับอากาศ' : 'เปิดเครื่องปรับอากาศ';
    case 'radio': return audio.playing ? 'ปิดเสียงบรรยากาศ' : 'เปิดเสียงบรรยากาศ';
    default: return objects.find(o => o.id === id)!.action;
  }
};
function renderDetails(id: ObjectId | null) {
  $('#mobile-selection').hidden = !id;
  document.querySelectorAll<HTMLButtonElement>('[data-object]').forEach(button => { const active = button.dataset.object === id; button.classList.toggle('selected', active); button.setAttribute('aria-pressed', String(active)); });
  if (!id || !room) {
    $('#details').innerHTML = `<div class="empty-detail">${icon('cube')}<h3>Every object has a story.</h3><p>คลิกจุดบนโมเดล หรือเลือกวัตถุด้านบน<br>เพื่อทดลองใช้งานในแบบของคุณ</p><span class="mini-label">EXPLORE AT YOUR OWN PACE</span></div>`;
    return;
  }
  const item = objects.find(o => o.id === id)!;
  $('#mobile-selection').innerHTML = `<span>${item.title}</span><button id="mobile-activate" aria-label="ใช้งาน${item.title}">${actionOf(id)} ${icon('arrow')}</button>`;
  $('#mobile-activate').onclick = () => { void activate(id); };
  let extra = '';
  if (id === 'drawers') extra = `<div class="drawer-picker" aria-label="เลือกชั้นลิ้นชัก">${[3, 2, 1, 0].map((n, i) => `<button data-drawer="${n}" class="${room!.state.drawer === n ? 'active' : ''}" aria-pressed="${room!.state.drawer === n}">ชั้น ${i + 1}</button>`).join('')}</div>`;
  if (id === 'ac') extra = `<label class="range-label">อุณหภูมิจำลอง <output id="temperature-output">${room.state.temperature}°C</output><input id="temperature" type="range" min="18" max="28" value="${room.state.temperature}" aria-label="อุณหภูมิจำลอง" /></label>`;
  if (id === 'radio') extra = `<label class="range-label">ระดับเสียง <output id="volume-output">${Math.round(audio.volume * 100)}%</output><input id="volume" type="range" min="0" max="100" value="${audio.volume * 100}" aria-label="ระดับเสียง" /></label>`;
  $('#details').innerHTML = `<div class="detail-heading"><span class="eyebrow">${item.tag}</span><button class="icon-button small" id="clear-selection" aria-label="ยกเลิกการเลือก">${icon('close')}</button></div><h3>${item.en}</h3><div class="detail-meta"><span>${item.title}</span><span id="object-state" class="object-state" data-state="${id}">${statusOf(id)}</span></div><p class="detail-description">${item.description}</p>${extra}<button class="primary-button" id="activate">${actionOf(id)}${icon('arrow')}</button><button class="focus-button" id="focus">${icon('zoom')} ดูใกล้ ๆ</button>`;
  $('#clear-selection').onclick = () => room!.select(null);
  $('#activate').onclick = () => { void activate(id); };
  $('#focus').onclick = () => room!.focus(id);
  document.querySelectorAll<HTMLButtonElement>('[data-drawer]').forEach(b => { b.onclick = () => room!.setDrawer(Number(b.dataset.drawer)); });
  if (id === 'ac') $('#temperature').oninput = event => {
    room!.state.temperature = Number((event.target as HTMLInputElement).value);
    $('#temperature-output').textContent = `${room!.state.temperature}°C`;
    $('#object-state').textContent = statusOf('ac');
  };
  if (id === 'radio') $('#volume').oninput = event => {
    audio.setVolume(Number((event.target as HTMLInputElement).value) / 100);
    $('#volume-output').textContent = `${Math.round(audio.volume * 100)}%`;
  };
}
async function activate(id: ObjectId) {
  if (!room?.ready) return;
  if (id === 'radio') {
    if (busyAudio) return; busyAudio = true;
    try { await audio.toggle(); } catch { toast('เบราว์เซอร์ยังไม่อนุญาตให้เล่นเสียง ลองกดอีกครั้ง'); }
    finally { busyAudio = false; }
  } else room.activate(id);
  updateState();
}
function updateState() {
  if (!room) return;
  if (room.selected) {
    const status = document.querySelector('#object-state'); if (status) status.textContent = statusOf(room.selected);
    const action = document.querySelector('#activate'); if (action) action.innerHTML = `${actionOf(room.selected)}${icon('arrow')}`;
    const mobileAction = document.querySelector('#mobile-activate'); if (mobileAction) mobileAction.innerHTML = `${actionOf(room.selected)}${icon('arrow')}`;
  }
  for (const mode of ['day', 'night'] as Mode[]) { $(`#${mode}`).classList.toggle('active', mode === room.mode); $(`#${mode}`).setAttribute('aria-pressed', String(mode === room.mode)); }
  document.querySelectorAll<HTMLButtonElement>('[data-object]').forEach(b => {
    const id = b.dataset.object as ObjectId;
    const active = (id === 'lamp' && room!.state.lamp) || (id === 'logo' && room!.state.logo) || (id === 'ac' && room!.state.ac) || (id === 'radio' && audio.playing);
    b.classList.toggle('is-on', active);
  });
}
const dialog = $<HTMLDialogElement>('#dialog');
function openDialog(content: string) { $('#dialog-content').innerHTML = content; dialog.showModal(); }
$('#close-dialog').onclick = () => dialog.close();
dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
$('#help').onclick = () => openDialog(`<div class="eyebrow">A QUICK GUIDE</div><h2 id="dialog-title">Welcome to your space.</h2><p>สำรวจห้องด้วยเมาส์ จอสัมผัส หรือแป้นพิมพ์</p><div class="help-row">${icon('move')}<div><strong>หมุนและเลื่อน</strong><p>ลากเพื่อหมุน · คลิกขวาแล้วลากเพื่อเลื่อน<br>บนมือถือ ใช้นิ้วเดียวหมุนและสองนิ้วเลื่อน</p></div></div><div class="help-row">${icon('zoom')}<div><strong>ซูมเข้าใกล้</strong><p>ใช้ล้อเมาส์หรือบีบสองนิ้ว · ดับเบิลคลิกวัตถุเพื่อดูใกล้ ๆ</p></div></div><div class="help-row">${icon('cube')}<div><strong>ลองใช้งานวัตถุ</strong><p>คลิกวัตถุหรือเลือกจากแผงควบคุม แล้วกดปุ่มใช้งาน<br>ใช้ Tab และ Enter เพื่อเลือกด้วยแป้นพิมพ์</p></div></div><div class="keyboard-note"><kbd>R</kbd> กลับมุมเริ่มต้น <kbd>Esc</kbd> ยกเลิกการเลือก</div>`);
$('#about').onclick = () => openDialog(`<div class="eyebrow">WEER / STUDIO 01</div><h2 id="dialog-title">Small space. Real possibilities.</h2><p>ห้องทำงานขนาด 3.5 × 3.5 เมตร สร้างจากโมเดล Blender เวอร์ชัน 02 ของคุณ พร้อมเฟอร์นิเจอร์ ต้นไม้ และรายละเอียดจากภาพอ้างอิง</p><p>วัตถุ 9 กลุ่มสามารถโต้ตอบได้ภายในเว็บ การควบคุมเครื่องปรับอากาศเป็นการจำลอง และเสียง ambient สร้างขึ้นในเบราว์เซอร์</p><div class="about-spec"><span>12.25 m²<small>FLOOR AREA</small></span><span>09<small>INTERACTIONS</small></span><span>01<small>YOUR STUDIO</small></span></div>`);
$('#settings').onclick = () => {
  if (!room?.ready) return;
  openDialog(`<div class="eyebrow">YOUR VIEW</div><h2 id="dialog-title">Make yourself comfortable.</h2><p>ปรับการแสดงผลให้เหมาะกับหน้าจอของคุณ</p><label class="range-label settings-range">ความสว่าง <output id="brightness-output">${Math.round(exposure * 100)}%</output><input id="brightness" type="range" min="70" max="150" value="${exposure * 100}" /></label><label class="setting-row">เงาของวัตถุ<input id="shadow-setting" type="checkbox" ${shadows ? 'checked' : ''} /></label><label class="setting-row">ความละเอียดสูง<input id="quality-setting" type="checkbox" ${highQuality ? 'checked' : ''} /></label><p class="settings-note">หากหมุนห้องแล้วกระตุก ลองปิดความละเอียดสูงหรือเงา</p>`);
  $('#brightness').oninput = event => { exposure = Number((event.target as HTMLInputElement).value) / 100; room!.setExposure(exposure); $('#brightness-output').textContent = `${Math.round(exposure * 100)}%`; };
  $('#shadow-setting').onchange = event => { shadows = (event.target as HTMLInputElement).checked; room!.setShadows(shadows); };
  $('#quality-setting').onchange = event => { highQuality = (event.target as HTMLInputElement).checked; room!.setQuality(highQuality); };
};
$('#brand').onclick = $('#reset-camera').onclick = () => {
  if (!room?.ready) return; room.setView('overview'); updateViewButtons('overview'); toast('กลับมุมเริ่มต้นแล้ว');
};
function updateViewButtons(view?: View) { document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b => { const active = b.dataset.view === view; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); }); }
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b => { b.onclick = () => { if (!room?.ready) return; room.setView(b.dataset.view as View); updateViewButtons(b.dataset.view as View); }; });
document.querySelectorAll<HTMLButtonElement>('[data-object]').forEach(b => { b.onclick = () => room?.select(b.dataset.object as ObjectId); });
for (const mode of ['day', 'night'] as Mode[]) $(`#${mode}`).onclick = () => { if (room?.ready) room.setMode(mode); };
$('#labels').onclick = () => {
  if (!room) return; room.showLabels = !room.showLabels;
  $('#labels').setAttribute('aria-pressed', String(room.showLabels)); $('#labels').setAttribute('aria-label', room.showLabels ? 'ซ่อนจุดเลือกวัตถุ' : 'แสดงจุดเลือกวัตถุ');
};
$('#tour').onclick = () => { if (room?.ready) room.toggleTour(); };
$('#fullscreen').onclick = async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await $('.experience').requestFullscreen(); }
  catch { toast('เบราว์เซอร์นี้ไม่รองรับการแสดงผลเต็มหน้าจอ'); }
};
document.addEventListener('fullscreenchange', () => $('#fullscreen').setAttribute('aria-label', document.fullscreenElement ? 'ออกจากเต็มหน้าจอ' : 'ขยายเต็มหน้าจอ'));
document.addEventListener('keydown', event => {
  if (dialog.open || (event.target as HTMLElement).matches('input, textarea, select') || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key.toLowerCase() === 'r') { room?.setView('overview'); updateViewButtons('overview'); }
  if (event.key === 'Escape') room?.select(null);
});
function showError(message: string) {
  $('#loading').hidden = false;
  $('#loading').innerHTML = `${icon('cube')}<h3>เปิดห้องไม่สำเร็จ</h3><p>${message}</p><button class="primary-button" id="retry">ลองอีกครั้ง ${icon('reset')}</button>`;
  $('#retry').onclick = () => location.reload();
  $('#system-status').textContent = 'ยังไม่พร้อมใช้งาน';
  document.querySelectorAll<HTMLButtonElement>('[data-object]').forEach(b => b.disabled = true);
}
$('#stage').addEventListener('studio-error', event => showError((event as CustomEvent<string>).detail));
try {
  room = new StudioRoom($('#stage'), $('#hotspots'));
  room.onSelect = renderDetails;
  room.onState = updateState;
  room.onCamera = () => {
    if (!room) return;
    $('#tour').innerHTML = icon(room.touring ? 'pause' : 'play');
    $('#tour').setAttribute('aria-label', room.touring ? 'หยุดชมรอบห้อง' : 'เริ่มชมรอบห้อง');
    $('#tour').setAttribute('aria-pressed', String(room.touring));
  };
  room.onHover = (id, x, y) => {
    const tooltip = $('#tooltip'); tooltip.hidden = !id;
    if (id) { tooltip.textContent = objects.find(o => o.id === id)!.title; tooltip.style.left = `${Math.min(x + 14, window.innerWidth - 150)}px`; tooltip.style.top = `${y - 36}px`; }
  };
  await room.load(progress => { $('#progress').style.width = `${progress * 100}%`; $('#progress-label').textContent = `${Math.round(progress * 100)}%`; });
  $('#loading').hidden = true;
  document.querySelectorAll<HTMLButtonElement>('[data-object]').forEach(b => b.disabled = false);
  $('#system-status').textContent = 'พร้อมให้คุณสำรวจ'; updateState();
  if (import.meta.env.DEV) Object.assign(window, { __studio: { room, audio, stats: () => room!.getStats(), select: (id: ObjectId) => room!.select(id), project: (id: ObjectId) => room!.project(id) } });
} catch (error) {
  console.error(error);
  showError('กรุณาตรวจสอบการเชื่อมต่อและการรองรับ WebGL ของเบราว์เซอร์');
}
window.addEventListener('pagehide', () => { void audio.stop(); });
if (import.meta.hot) import.meta.hot.dispose(() => { room?.dispose(); audio.dispose(); });
