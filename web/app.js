'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const app = $('#app');
const state = { user: null, page: 'spaces', date: dateString(), capacity: '', equipment: '', rooms: [], bookings: [], notifications: [], members: [], scope: 'mine', bookingDraft: null, editingRoom: null, cancelId: null, loading: false, loadError: '', loadToken: 0, identityGeneration: 0, identityPending: false };
const equipmentOptions = ['显示屏', '白板', '视频会议', '电话会议'];
const icons = { spaces: '▦', bookings: '▤', inbox: '◷', manage: '⚙' };
const pageNames = { spaces: '会议室', bookings: '我的预约', inbox: '通知中心', manage: '空间管理' };
const art = `<div class="room-art" aria-hidden="true"><div class="art-wall"></div><div class="art-window"></div><div class="art-board"></div><div class="art-chair one"></div><div class="art-chair two"></div><div class="art-table"></div><div class="art-chair three"></div><div class="art-plant"></div></div>`;
const brand = `<div class="brand"><span class="brand-mark" aria-hidden="true">m</span><span>MeetSpace<small>ROOM FOR IDEAS</small></span></div>`;

function escapeHtml(value) { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function dateString(date = new Date()) { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date); }
function timeString(value) { return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)); }
function prettyDate(value) { return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: 'long', day: 'numeric', weekday: 'long' }).format(new Date(`${value}T12:00:00+08:00`)); }
function fullDate(value) { return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(value)); }
function option(value, current) { return `<option value="${escapeHtml(value)}" ${value === current ? 'selected' : ''}>${escapeHtml(value)}</option>`; }
function toast(message) { $('#toast').textContent = message; $('#toast').classList.add('visible'); clearTimeout(toast.timer); toast.timer = setTimeout(() => $('#toast').classList.remove('visible'), 4500); }

async function api(path, method = 'GET', data) {
  const identityGeneration = state.identityGeneration;
  const response = await fetch(`/api${path}`, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Meeting-App': '1' }, ...(data === undefined ? {} : { body: JSON.stringify(data) }) });
  let result;
  try { result = await response.json(); } catch { throw new Error('服务返回异常，请稍后重试'); }
  if (!response.ok) {
    if (response.status === 401 && path !== '/login' && identityGeneration === state.identityGeneration) {
      state.identityGeneration++;
      state.user = null;
      state.identityPending = false;
      document.querySelectorAll('dialog[open]').forEach(dialog => dialog.close());
      renderLogin();
    }
    const error = new Error(result.error || '请求失败，请稍后重试');
    error.status = response.status;
    throw error;
  }
  return result;
}

function renderLogin() {
  app.innerHTML = `<div class="login-page"><section class="login-story">${brand}<div><span class="eyebrow">GOOD IDEAS NEED A PLACE</span><h1>给好想法<br>一个空间。</h1><p>少一点日程往返，多一点专注协作。<br>在这里，为下一场讨论找到合适的地方。</p><div class="login-art-wrap">${art}</div></div><div class="login-story-footer">空间连接彼此，想法由此发生。<br>MeetSpace · 团队空间预约</div></section><main class="login-main"><div class="login-box"><span class="eyebrow">WELCOME TO MEETSPACE</span><h2>欢迎回来</h2><p class="muted">登录你的团队，开始一场有准备的会议。</p><form id="login-form" class="login-form"><label>工作邮箱<input name="email" type="email" autocomplete="username" placeholder="name@company.com" required></label><label>密码<input name="password" type="password" autocomplete="current-password" placeholder="输入密码" required></label><p id="login-error" class="form-error" role="alert"></p><button class="button primary full" type="submit">登录工作空间 <span aria-hidden="true">↗</span></button></form><div class="demo-accounts"><p>示例账号 · 点击填入，再登录<br>统一密码：<code>MeetSpace!2026</code></p><div class="account-buttons"><button data-account="admin">林可 · 管理员</button><button data-account="alice">陈悦 · 成员</button><button data-account="bob">周言 · 成员</button><button data-account="other">许宁 · 另一团队</button></div></div><div class="login-footnote">本地示例工作空间 · 数据保存在本机<br>所有会议时间均使用北京时间（UTC+8）</div></div></main></div>`;
  $('#login-form').addEventListener('submit', login);
  document.querySelectorAll('[data-account]').forEach(button => button.addEventListener('click', () => {
    $('#login-form [name=email]').value = `${button.dataset.account}@meetspace.test`;
    $('#login-form [name=password]').value = 'MeetSpace!2026';
    $('#login-error').textContent = '';
  }));
}

async function login(event) {
  event.preventDefault();
  state.identityGeneration++;
  const form = event.currentTarget, submit = $('button[type=submit]', form);
  submit.disabled = true; $('#login-error').textContent = '';
  try {
    await api('/login', 'POST', { email: form.elements.email.value, password: form.elements.password.value });
    state.user = (await api('/session')).user;
    state.identityPending = false;
    state.page = 'spaces'; state.scope = 'mine'; state.rooms = []; state.bookings = []; state.notifications = []; state.members = [];
    await loadPage();
  } catch (error) { const target = $('#login-error'); if (target) target.textContent = error.message; }
  finally { submit.disabled = false; }
}

async function loadPage() {
  if (!state.user) return;
  const token = ++state.loadToken;
  state.loading = true; state.loadError = '';
  renderShell();
  try {
    if (state.identityPending) {
      const session = await api('/session');
      if (token !== state.loadToken || !state.user) return;
      state.user = session.user; state.identityPending = false;
      if (state.user.role !== 'admin') { state.page = 'spaces'; state.scope = 'mine'; }
    }
    const params = `?date=${encodeURIComponent(state.date)}`;
    const requests = [api(`/rooms${params}`), api(`/bookings?scope=${state.scope}`), api('/notifications')];
    if (state.page === 'manage' && state.user.role === 'admin') requests.push(api('/members'));
    const [rooms, bookings, notifications, members] = await Promise.all(requests);
    if (token !== state.loadToken || !state.user) return;
    state.rooms = rooms.rooms; state.bookings = bookings.bookings; state.notifications = notifications.notifications; state.members = members?.members || [];
  } catch (error) {
    if (token !== state.loadToken || !state.user) return;
    state.loadError = error.message;
  } finally {
    if (token === state.loadToken && state.user) { state.loading = false; renderShell(); }
  }
}

function renderShell() {
  if (!state.user) return;
  const user = state.user, unread = state.notifications.filter(n => !n.read).length;
  const nav = ['spaces', 'bookings', 'inbox', ...(user.role === 'admin' ? ['manage'] : [])].map(page => `${page === 'manage' ? '<div class="nav-group manage-label"></div>' : ''}<button data-page="${page}" class="${state.page === page ? 'active' : ''}" ${state.page === page ? 'aria-current="page"' : ''}><span class="nav-icon" aria-hidden="true">${icons[page]}</span>${pageNames[page]}${page === 'inbox' && unread ? `<span class="nav-badge">${unread}</span>` : ''}</button>`).join('');
  app.innerHTML = `<aside class="sidebar">${brand}<div class="workspace"><span class="workspace-symbol" aria-hidden="true">◈</span><div>${escapeHtml(user.team_name)}<small>TEAM WORKSPACE</small></div></div><div class="nav-label">工作空间</div><nav class="nav" aria-label="工作空间导航">${nav}</nav><div class="sidebar-bottom"><div class="sidebar-note"><span class="eyebrow">MAKE ROOM FOR BETTER</span><p>准时开始，留好空间。<br>不用的预约记得及时取消。</p></div><div class="profile"><span class="avatar">${escapeHtml(user.name.slice(-1))}</span><div class="profile-name">${escapeHtml(user.name)}<small>${user.role === 'admin' ? '团队管理员' : '团队成员'}</small></div><button data-logout class="logout">退出</button></div></div></aside><main class="main"><header class="topbar"><div class="topbar-title">工作空间 <span aria-hidden="true">/</span> <strong>${pageNames[state.page]}</strong></div><div class="mobile-brand brand"><span class="brand-mark" aria-hidden="true">m</span>MeetSpace</div><div class="topbar-right"><span><span class="live-dot"></span>北京时间 UTC+8</span><span class="version">${escapeHtml(user.team_name)}</span><button data-logout class="logout" aria-label="退出登录">退出</button></div></header><div class="content">${state.loadError ? `<div class="retry-panel" role="alert">${escapeHtml(state.loadError)}<br><button data-refresh class="button secondary">重新加载</button></div>` : state.loading ? '<div class="empty">正在同步工作空间…</div>' : pageContent()}<footer class="page-footer"><span>为团队的下一次好想法，留一个空间。</span><span>MeetSpace · ${escapeHtml(user.team_name)}</span></footer></div></main>`;
  document.querySelectorAll('[data-page]').forEach(button => button.addEventListener('click', () => { state.page = button.dataset.page; state.scope = 'mine'; loadPage(); }));
  document.querySelectorAll('[data-logout]').forEach(button => button.addEventListener('click', logout));
  document.querySelectorAll('[data-refresh]').forEach(button => button.addEventListener('click', loadPage));
  wirePage();
}

function pageContent() {
  if (state.page === 'spaces') return spacesContent();
  if (state.page === 'bookings') return bookingsContent();
  if (state.page === 'inbox') return inboxContent();
  if (state.page === 'manage') return manageContent();
  return '';
}

function heading(eyebrow, title, subtitle, aside = '') {
  return `<div class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p class="muted">${subtitle}</p></div>${aside}</div>`;
}

function spacesContent() {
  const rooms = state.rooms.filter(room => room.active && (!state.capacity || room.capacity >= Number(state.capacity)) && (!state.equipment || room.equipment.includes(state.equipment)));
  const myToday = state.bookings.filter(b => b.status === 'confirmed' && dateString(new Date(b.start)) === state.date).length;
  const totalToday = state.rooms.reduce((sum, room) => sum + room.bookings.length, 0);
  return `${heading('YOUR SPACE, YOUR IDEAS', '找到你的下一场好会议', '选一个合适的空间，让讨论自然发生。', `<div class="heading-aside"><strong>${state.date.slice(5).replace('-', ' / ')}</strong>${prettyDate(state.date).split('日')[1] || ''}</div>`)}<section class="hero"><div class="hero-copy"><span class="eyebrow">ROOM FOR WHAT’S NEXT</span><h2>从一个想法，<br>到一场值得期待的讨论。</h2><p>小组碰头、远程协作、项目共创。<br>为不同的会议，找到刚刚好的空间。</p></div>${art}</section><div class="stats"><div class="stat"><div><p class="stat-label">可预约会议室</p><p class="stat-value">${state.rooms.filter(r => r.active).length}<small>间</small></p></div><span class="stat-icon" aria-hidden="true">▦</span></div><div class="stat"><div><p class="stat-label">所选日期预约</p><p class="stat-value">${totalToday}<small>场</small></p></div><span class="stat-icon" aria-hidden="true">◷</span></div><div class="stat"><div><p class="stat-label">我的当日会议</p><p class="stat-value">${myToday}<small>场</small></p></div><span class="stat-icon" aria-hidden="true">▤</span></div></div><section><div class="section-top"><div><h2>为下一场会议选个空间</h2><p>查看当天日程，再选择你的预约时段。</p></div><div class="toolbar"><input id="filter-date" aria-label="查看日期" type="date" value="${state.date}"><select id="filter-capacity" aria-label="按参会人数筛选"><option value="">所有容量</option>${[4, 6, 8, 12].map(n => `<option value="${n}" ${state.capacity === String(n) ? 'selected' : ''}>${n} 人及以上</option>`).join('')}</select><select id="filter-equipment" aria-label="按设备筛选"><option value="">所有设备</option>${equipmentOptions.map(e => option(e, state.equipment)).join('')}</select></div></div><div class="rooms-grid">${rooms.length ? rooms.map(roomCard).join('') : '<div class="empty"><strong>没有符合条件的会议室</strong>试试调整容量或设备筛选。</div>'}</div></section>`;
}

function roomCard(room, index) {
  const slots = Array.from({ length: 48 }, (_, slot) => {
    const start = new Date(`${state.date}T08:00:00+08:00`).getTime() + slot * 15 * 60000;
    return room.bookings.some(b => new Date(b.start).getTime() < start + 15 * 60000 && new Date(b.end).getTime() > start);
  });
  const summary = room.bookings.length ? `${room.bookings.length} 场会议 · ${room.bookings.map(b => `${timeString(b.start)}–${timeString(b.end)}`).join('、')}` : '当天暂无预约';
  const agenda = room.bookings.length ? `<details class="room-agenda"><summary>查看当日日程 · ${room.bookings.length}</summary><ul>${room.bookings.map(b => `<li><strong>${timeString(b.start)}–${timeString(b.end)}</strong><span>${escapeHtml(b.title)} · ${escapeHtml(b.owner)}</span></li>`).join('')}</ul></details>` : '';
  return `<article class="room-card"><div class="room-card-top"><span class="room-symbol tone-${index % 4}" aria-hidden="true">${['▱', '◫', '▥', '▧'][index % 4]}</span><div class="room-info"><h3>${escapeHtml(room.name)}</h3><p>${escapeHtml(room.location)} <span aria-hidden="true">·</span> ${room.capacity} 人</p></div><span class="status-pill ${room.active ? '' : 'off'}">${room.active ? '开放预约' : '已停用'}</span></div><div class="room-details"><div class="equipment">${room.equipment.length ? room.equipment.map(e => `<span>${escapeHtml(e)}</span>`).join('') : '<span>基础会议空间</span>'}</div><div class="timeline-label"><span>08:00</span><span>12:00</span><span>16:00</span><span>20:00</span></div><div class="timeline" role="img" aria-label="${escapeHtml(summary)}" title="${escapeHtml(summary)}">${slots.map(occupied => `<span class="${occupied ? 'occupied' : ''}"></span>`).join('')}</div>${agenda}</div><div class="room-footer"><p>${state.page === 'manage' ? `容量 ${room.capacity} 人 · ${room.active ? '允许新预约' : '已暂停新预约'}` : `${room.bookings.length ? `当天已有 ${room.bookings.length} 场预约` : '当天暂无预约'} · 绿色为已占用`}</p>${state.page === 'manage' ? `<button class="button secondary small" data-edit-room="${room.id}" aria-label="编辑${escapeHtml(room.name)}">编辑空间</button>` : `<button class="button primary small" data-book-room="${room.id}" aria-label="预约${escapeHtml(room.name)}">预约空间 <span aria-hidden="true">↗</span></button>`}</div></article>`;
}

function bookingsContent() {
  const upcoming = state.bookings.filter(b => b.status === 'confirmed' && new Date(b.end) > new Date()).sort((a, b) => new Date(a.start) - new Date(b.start));
  const history = state.bookings.filter(b => b.status === 'cancelled' || new Date(b.end) <= new Date());
  return `${heading('YOUR MEETINGS', state.scope === 'team' ? '团队的每一场讨论' : '让每一场讨论，都有安排', '查看即将开始的会议，及时释放不再需要的时段。', state.user.role === 'admin' ? `<div class="tabs" aria-label="预约查看范围"><button data-scope="mine" class="${state.scope === 'mine' ? 'active' : ''}">我的预约</button><button data-scope="team" class="${state.scope === 'team' ? 'active' : ''}">团队预约</button></div>` : '')}<div class="section-top"><h2>即将进行 <span class="muted">· ${upcoming.length}</span></h2><button data-refresh class="button secondary small">刷新日程</button></div><div class="list-panel">${upcoming.length ? upcoming.map(bookingRow).join('') : '<div class="empty"><strong>日程留白，想法待发生</strong>去会议室页面，为下一次讨论预约空间。</div>'}</div><div class="section-top manage-heading"><h2>历史与已取消 <span class="muted">· ${history.length}</span></h2></div><div class="list-panel">${history.length ? history.map(bookingRow).join('') : '<div class="empty">暂无历史预约</div>'}</div>`;
}

function bookingRow(booking) {
  const day = dateString(new Date(booking.start));
  const canCancel = booking.status === 'confirmed' && new Date(booking.start) > new Date();
  const status = booking.status === 'cancelled' ? '已取消' : new Date(booking.end) <= new Date() ? '已结束' : new Date(booking.start) <= new Date() ? '进行中' : '已确认';
  return `<article class="booking-row"><div class="date-tile">${Number(day.slice(5, 7))} 月<strong>${day.slice(8)}</strong></div><div class="booking-info"><h3>${escapeHtml(booking.title)}</h3><p>${timeString(booking.start)}–${timeString(booking.end)} · ${escapeHtml(booking.room_name)} · ${escapeHtml(booking.location)}<br>${escapeHtml(booking.owner)} · ${booking.attendees} 人 · 预约 #${booking.id}</p></div><div class="booking-actions"><span class="status-pill ${booking.status === 'cancelled' ? 'cancelled' : ''}">${status}</span>${canCancel ? `<button data-cancel="${booking.id}" class="button secondary small" aria-label="取消${escapeHtml(booking.title)}">取消预约</button>` : ''}</div></article>`;
}

function inboxContent() {
  const unread = state.notifications.filter(n => !n.read).length;
  return `${heading('STAY IN THE LOOP', '每一个安排，都有回音', '你的预约确认与取消记录，都在这里。', `<button id="mark-read" class="button secondary" ${unread ? '' : 'disabled'}>全部标为已读</button>`)}<div class="list-panel">${state.notifications.length ? state.notifications.map(n => `<article class="notice-row"><span class="notice-dot ${n.read ? 'read' : ''}" aria-label="${n.read ? '已读' : '未读'}"></span><div><p>${escapeHtml(n.message)}</p><small>${fullDate(n.created_at)} · 预约 #${n.booking_id}</small></div></article>`).join('') : '<div class="empty"><strong>暂时没有新消息</strong>完成预约后，你会在这里收到确认。</div>'}</div>`;
}

function manageContent() {
  return `${heading('WORKSPACE SETTINGS', '让空间，为团队更好地运转', '维护会议室信息，为成员分配合适的管理权限。', '<button id="add-room" class="button primary">＋ 添加会议室</button>')}<div class="section-top"><h2>团队空间 <span class="muted">· ${state.rooms.length}</span></h2><p>停用空间将阻止新预约，已有预约继续保留。</p></div><div class="rooms-grid">${state.rooms.map(roomCard).join('')}</div><div class="section-top manage-heading"><div><h2>成员与权限</h2><p>角色变更将在成员下一次请求时生效；团队至少保留一位管理员。</p></div></div><div class="list-panel">${state.members.map(member => `<div class="member-row"><span class="avatar">${escapeHtml(member.name.slice(-1))}</span><div class="member-info"><p>${escapeHtml(member.name)}${member.id === state.user.id ? ' <span class="muted">· 你</span>' : ''}</p><small>${escapeHtml(member.email)}</small></div><select data-member="${member.id}" aria-label="${escapeHtml(member.name)}的角色"><option value="member" ${member.role === 'member' ? 'selected' : ''}>团队成员</option><option value="admin" ${member.role === 'admin' ? 'selected' : ''}>管理员</option></select></div>`).join('')}</div>`;
}

function wirePage() {
  $('#filter-date')?.addEventListener('change', event => { if (event.target.value) { state.date = event.target.value; loadPage(); } });
  $('#filter-capacity')?.addEventListener('change', event => { state.capacity = event.target.value; renderShell(); });
  $('#filter-equipment')?.addEventListener('change', event => { state.equipment = event.target.value; renderShell(); });
  document.querySelectorAll('[data-book-room]').forEach(button => button.addEventListener('click', () => openBooking(Number(button.dataset.bookRoom))));
  document.querySelectorAll('[data-edit-room]').forEach(button => button.addEventListener('click', () => openRoom(Number(button.dataset.editRoom))));
  document.querySelectorAll('[data-cancel]').forEach(button => button.addEventListener('click', () => openCancel(Number(button.dataset.cancel))));
  document.querySelectorAll('[data-scope]').forEach(button => button.addEventListener('click', () => { state.scope = button.dataset.scope; loadPage(); }));
  document.querySelectorAll('[data-member]').forEach(select => select.addEventListener('change', changeRole));
  $('#add-room')?.addEventListener('click', () => openRoom(null));
  $('#mark-read')?.addEventListener('click', async event => {
    event.currentTarget.disabled = true;
    try { await api('/notifications/read', 'POST', {}); await loadPage(); toast('通知已标为已读'); }
    catch (error) { toast(error.message); if (state.user) renderShell(); }
  });
}

async function logout(event) {
  const button = event.currentTarget;
  button.disabled = true;
  try { await api('/logout', 'POST', {}); state.identityGeneration++; state.identityPending = false; state.loadToken++; state.user = null; document.querySelectorAll('dialog[open]').forEach(d => d.close()); renderLogin(); }
  catch (error) { toast(error.message); button.disabled = false; }
}

function defaultTimes(day) {
  const now = new Date(), localTime = timeString(now);
  let minutes = day === dateString(now) ? Math.ceil((Number(localTime.slice(0, 2)) * 60 + Number(localTime.slice(3)) + 1) / 15) * 15 : 9 * 60;
  let chosenDay = day;
  if (day < dateString(now) || minutes >= 20 * 60) {
    chosenDay = dateString(new Date(now.getTime() + 86400000)); minutes = 9 * 60;
  }
  minutes = Math.max(8 * 60, minutes);
  const format = value => `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
  return { day: chosenDay, start: format(minutes), end: format(Math.min(minutes + 60, 20 * 60)) };
}

function openBooking(roomId) {
  const room = state.rooms.find(r => r.id === roomId), form = $('#booking-form');
  form.reset();
  const times = defaultTimes(state.date);
  form.elements.date.min = dateString();
  form.elements.date.max = dateString(new Date(Date.now() + 30 * 86400000));
  form.elements.date.value = times.day; form.elements.start.value = times.start; form.elements.end.value = times.end;
  form.elements.attendees.max = room.capacity; form.elements.attendees.value = Math.min(2, room.capacity);
  $('#booking-title').textContent = `预约 ${room.name}`;
  $('#booking-subtitle').textContent = `${room.location} · 最多 ${room.capacity} 人`;
  $('#booking-error').textContent = '';
  state.bookingDraft = { roomId, fingerprint: '', key: '' };
  $('#booking-dialog').showModal();
}

$('#booking-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget, submit = $('button[type=submit]', form), draft = state.bookingDraft;
  submit.disabled = true; $('#booking-error').textContent = '';
  const payload = { room_id: draft.roomId, title: form.elements.title.value.trim(), attendees: Number(form.elements.attendees.value), start: `${form.elements.date.value}T${form.elements.start.value}:00+08:00`, end: `${form.elements.date.value}T${form.elements.end.value}:00+08:00` };
  const fingerprint = JSON.stringify(payload);
  if (draft.fingerprint !== fingerprint) { draft.fingerprint = fingerprint; draft.key = crypto.randomUUID(); }
  try {
    const result = await api('/bookings', 'POST', { ...payload, idempotency_key: draft.key });
    $('#booking-dialog').close(); state.date = form.elements.date.value;
    await loadPage(); toast(`预约成功 · #${result.booking.id}，确认已发送至通知中心`);
  } catch (error) { $('#booking-error').textContent = error.message; }
  finally { submit.disabled = false; }
});

function openRoom(roomId) {
  const room = state.rooms.find(r => r.id === roomId), form = $('#room-form');
  form.reset(); state.editingRoom = roomId;
  $('#room-title').textContent = room ? `编辑 ${room.name}` : '添加会议室';
  $('#room-error').textContent = '';
  if (room) {
    form.elements.name.value = room.name; form.elements.location.value = room.location; form.elements.capacity.value = room.capacity; form.elements.active.checked = room.active;
    form.querySelectorAll('[name=equipment]').forEach(input => { input.checked = room.equipment.includes(input.value); });
  }
  $('#room-dialog').showModal();
}

$('#room-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget, submit = $('button[type=submit]', form);
  submit.disabled = true; $('#room-error').textContent = '';
  const data = { name: form.elements.name.value, location: form.elements.location.value, capacity: Number(form.elements.capacity.value), active: form.elements.active.checked, equipment: Array.from(form.querySelectorAll('[name=equipment]:checked'), input => input.value) };
  try {
    await api(state.editingRoom ? `/rooms/${state.editingRoom}` : '/rooms', state.editingRoom ? 'PATCH' : 'POST', data);
    $('#room-dialog').close(); await loadPage(); toast('会议室已保存');
  } catch (error) { $('#room-error').textContent = error.message; }
  finally { submit.disabled = false; }
});

function openCancel(id) {
  const booking = state.bookings.find(b => b.id === id);
  state.cancelId = id;
  $('#confirm-copy').textContent = `「${booking.title}」 · ${fullDate(booking.start)} · ${booking.room_name}。取消后，该时段将重新开放预约。`;
  $('#confirm-error').textContent = '';
  $('#confirm-dialog').showModal();
}

$('#confirm-cancel').addEventListener('click', async event => {
  const button = event.currentTarget; button.disabled = true;
  try { await api(`/bookings/${state.cancelId}/cancel`, 'POST', {}); $('#confirm-dialog').close(); await loadPage(); toast('预约已取消，时段已释放'); }
  catch (error) { $('#confirm-error').textContent = error.message; }
  finally { button.disabled = false; }
});

async function changeRole(event) {
  const select = event.currentTarget; select.disabled = true;
  try {
    await api(`/members/${select.dataset.member}`, 'PATCH', { role: select.value });
    state.identityPending = true;
    if (Number(select.dataset.member) === state.user.id && select.value === 'member') {
      state.user = { ...state.user, role: 'member' }; state.page = 'spaces'; state.scope = 'mine';
    }
    state.user = (await api('/session')).user;
    state.identityPending = false;
    if (state.user.role !== 'admin') { state.page = 'spaces'; state.scope = 'mine'; }
    await loadPage(); toast('成员角色已更新');
  } catch (error) {
    toast(error.message);
    if (state.user) {
      if (state.identityPending) { state.loadError = error.message; renderShell(); }
      else await loadPage();
    }
  }
}

document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } }));

(async function start() {
  try { state.user = (await api('/session')).user; await loadPage(); }
  catch (error) {
    if (error.status === 401) renderLogin();
    else app.innerHTML = `<main class="error-page"><h2>暂时无法连接工作空间</h2><p class="muted">${escapeHtml(error.message)}</p><p>请检查本地服务后刷新页面。</p></main>`;
  }
})();
