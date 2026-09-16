const state = {
  date: new Date(),
  habits: [],
  filter: 'all',
  archived: false,
  view: 'today',
  user: JSON.parse(localStorage.getItem('day-by-day-user') || 'null'),
  editingHabitId: null,
};

const $ = (selector) => document.querySelector(selector);
const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.user) headers['X-User-ID'] = String(state.user.id);
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    let message = 'Something went wrong.';
    try { message = (await response.json()).detail || message; } catch (_) {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
};
const isoDate = (date) => date.toISOString().slice(0, 10);
const displayDate = (date) => date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
const apiDate = () => isoDate(state.date);
const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));

function setAuthMode(mode) {
  document.querySelectorAll('[data-auth-mode]').forEach((button) => button.classList.toggle('active', button.dataset.authMode === mode));
  $('#loginPane').classList.toggle('hidden', mode !== 'login');
  $('#signupPane').classList.toggle('hidden', mode !== 'signup');
}

function enterApp(user) {
  state.user = user;
  localStorage.setItem('day-by-day-user', JSON.stringify(user));
  $('#authScreen').classList.add('hidden');
  $('.app-shell').classList.remove('hidden');
  $('#currentUserName').textContent = user.name;
  setView('today');
  loadHabits();
}

function logout() {
  localStorage.removeItem('day-by-day-user');
  state.user = null;
  $('.app-shell').classList.add('hidden');
  $('#authScreen').classList.remove('hidden');
  setAuthMode('login');
}

async function login(event) {
  event.preventDefault();
  const name = new FormData(event.target).get('name').trim().toLowerCase();
  const users = await fetch('/api/users').then((response) => response.json());
  const user = users.find((item) => item.name.toLowerCase() === name);
  if (!user) { $('#loginError').textContent = 'We could not find that account. Try signing up.'; return; }
  enterApp(user);
}

async function signup(event) {
  event.preventDefault();
  const name = new FormData(event.target).get('name').trim();
  try {
    const user = await api('/api/users', { method: 'POST', body: JSON.stringify({ name }) });
    enterApp(user);
  } catch (error) { $('#signupError').textContent = error.message; }
}

function setView(view) {
  state.view = view;
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === view));
  $('.hero-grid').classList.toggle('hidden', view !== 'today');
  $('.checklist-section').classList.toggle('hidden', view !== 'today');
  $('#historyView').classList.toggle('hidden', view !== 'history');
  $('#manageView').classList.toggle('hidden', view !== 'manage');
  if (view === 'history') loadHistory();
  if (view === 'manage') loadManageHabits();
  $('.sidebar').classList.remove('open');
  lucide.createIcons();
}

function setTodayDate() {
  $('#dateEyebrow').textContent = displayDate(state.date).toUpperCase();
  const hour = new Date().getHours();
  $('#pageTitle').textContent = `${hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'}, Ananya.`;
}

function render() {
  const visible = state.habits.filter((habit) => state.filter === 'all' || (state.filter === 'done' ? habit.completed : !habit.completed));
  const completed = state.habits.filter((habit) => habit.completed).length;
  const pending = state.habits.length - completed;
  const percent = state.habits.length ? Math.round((completed / state.habits.length) * 100) : 0;
  const best = state.habits.reduce((highest, habit) => Math.max(highest, habit.best_streak), 0);

  $('#habitCount').textContent = state.habits.length;
  $('#allCount').textContent = state.habits.length;
  $('#pendingCount').textContent = pending;
  $('#doneCount').textContent = completed;
  $('#progressPercent').textContent = `${percent}%`;
  $('#progressRing').style.background = `conic-gradient(#fff ${percent * 3.6}deg, rgba(255,255,255,.17) 0deg)`;
  $('#bestStreak').textContent = best;
  $('#streakCaption').textContent = best ? 'Your consistency is adding up.' : 'Start with one checkmark.';
  $('#reminderText').textContent = pending ? `${pending} ${pending === 1 ? 'habit is' : 'habits are'} waiting for you. You know what to do.` : 'Everything is checked off. That feels good.';
  $('#heroHeading').textContent = pending ? 'Make today count.' : 'You did it today.';
  $('#habitList').innerHTML = visible.map((habit, index) => habitCard(habit, index)).join('');
  $('#emptyState').classList.toggle('hidden', visible.length !== 0);
  if (!visible.length) {
    $('#emptyTitle').textContent = state.habits.length ? 'Nothing in this view.' : state.archived ? 'No archived habits.' : 'A blank slate.';
    $('#emptyText').textContent = state.habits.length ? 'Try another filter to find your habits.' : state.archived ? 'Your active habits are all still in the rhythm.' : 'Add a habit to give your morning a little shape.';
    $('#emptyAction').classList.toggle('hidden', Boolean(state.habits.length || state.archived));
  }
  lucide.createIcons();
}

function habitCard(habit, index) {
  return `<article class="habit-row ${habit.completed ? 'completed' : ''}" style="animation-delay:${index * 45}ms">
    <button class="habit-check" data-complete="${habit.id}" aria-label="${habit.completed ? 'Uncheck' : 'Complete'} ${escapeHtml(habit.name)}"><i data-lucide="check"></i></button>
    <div><span class="habit-name">${escapeHtml(habit.name)}</span>${habit.description ? `<span class="habit-description">${escapeHtml(habit.description)}</span>` : ''}</div>
    <div class="habit-streak"><i data-lucide="flame"></i><span><strong>${habit.current_streak}</strong> day streak · best ${habit.best_streak}</span></div>
    <button class="habit-menu" data-archive="${habit.id}" aria-label="Archive ${escapeHtml(habit.name)}"><i data-lucide="archive"></i></button>
  </article>`;
}

async function loadHabits() {
  try {
    const payload = await api(`/api/today?date=${apiDate()}`);
    state.habits = payload.habits;
    setTodayDate();
    render();
  } catch (error) { showToast(error.message); }
}

async function loadHistory() {
  try {
    const habits = await api('/api/habits');
    const histories = await Promise.all(habits.map(async (habit) => ({ habit, completions: await api(`/api/completions/${habit.id}`) })));
    const total = histories.reduce((sum, item) => sum + item.completions.length, 0);
    const best = histories.reduce((highest, item) => Math.max(highest, item.completions.length ? 1 : 0), 0);
    $('#historySummary').innerHTML = `<div class="history-stat"><strong>${total}</strong><span>check-ins recorded</span></div><div class="history-stat"><strong>${habits.length}</strong><span>habits in your system</span></div><div class="history-stat"><strong>${best ? '✓' : '—'}</strong><span>showing up counts</span></div>`;
    const counts = [];
    for (let offset = 13; offset >= 0; offset -= 1) {
      const day = new Date(); day.setDate(day.getDate() - offset); const key = isoDate(day);
      counts.push({ label: day.toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 2), count: histories.reduce((sum, item) => sum + item.completions.filter((completion) => completion.date === key).length, 0) });
    }
    const max = Math.max(...counts.map((item) => item.count), 1);
    $('#activityChart').innerHTML = counts.map((item) => `<div class="chart-column"><span class="chart-value">${item.count || ''}</span><div class="chart-bar" style="height:${Math.max(item.count / max * 100, item.count ? 12 : 4)}%"></div><small>${item.label}</small></div>`).join('');
    $('#leaderList').innerHTML = histories.length ? histories.sort((a, b) => b.completions.length - a.completions.length).map((item) => `<div class="leader-row"><span class="leader-dot"></span><strong>${escapeHtml(item.habit.name)}</strong><span>${item.completions.length} logged</span></div>`).join('') : '<p class="empty-copy">Your first check-in will appear here.</p>';
    lucide.createIcons();
  } catch (error) { showToast(error.message); }
}

async function loadManageHabits() {
  try {
    const archived = document.querySelector('[data-manage-filter="archived"].active');
    const query = $('#habitSearch').value.trim();
    const params = new URLSearchParams({ archived: String(Boolean(archived)) });
    if (query) params.set('q', query);
    const habits = await api(`/api/habits?${params}`);
    $('#manageList').innerHTML = habits.length ? habits.map((habit) => `<div class="manage-row"><div><strong>${escapeHtml(habit.name)}</strong><span>${habit.frequency_type === 'daily' ? 'Every day' : `${habit.days_of_week.length} days a week`} · started ${habit.start_date}</span></div><div class="manage-actions"><button class="text-button" data-edit="${habit.id}" type="button"><i data-lucide="pencil"></i> Edit</button><button class="text-button" data-toggle-archive="${habit.id}" type="button"><i data-lucide="${archived ? 'rotate-ccw' : 'archive'}"></i> ${archived ? 'Restore' : 'Archive'}</button></div></div>`).join('') : '<div class="empty-state"><div class="empty-icon"><i data-lucide="sparkles"></i></div><h3>No habits here.</h3><p>Make a small promise and give it a place in your day.</p></div>';
    lucide.createIcons();
  } catch (error) { showToast(error.message); }
}

async function editHabit(id) {
  const habit = await api(`/api/habits/${id}`);
  state.editingHabitId = id;
  $('#modalTitle').textContent = 'Edit a habit';
  $('#habitForm').elements.name.value = habit.name;
  $('#habitForm').elements.description.value = habit.description || '';
  $('#habitForm').elements.start_date.value = habit.start_date;
  $('#habitForm').elements.end_date.value = habit.end_date || '';
  $('#habitForm').querySelector(`input[value="${habit.frequency_type}"]`).checked = true;
  $('#weekdayPicker').classList.toggle('hidden', habit.frequency_type !== 'custom');
  document.querySelectorAll('#weekdayPicker input').forEach((input) => { input.checked = habit.days_of_week.includes(Number(input.value)); });
  openModal();
}

async function loadArchived() {
  try {
    const habits = await api('/api/habits?archived=true');
    state.archived = true;
    state.habits = habits.map((habit) => ({ ...habit, completed: false, current_streak: 0, best_streak: 0 }));
    $('#checklistTitle').innerHTML = 'Archived habits <span id="habitCount">0</span>';
    $('#reminderText').textContent = 'Resting habits are kept here, never forgotten.';
    $('#heroHeading').textContent = 'Room to breathe.';
    setTodayDate();
    render();
  } catch (error) { showToast(error.message); }
}

async function toggleCompletion(id, completed) {
  try {
    if (completed) await api(`/api/completions/${id}?date=${apiDate()}`, { method: 'DELETE' });
    else await api('/api/completions', { method: 'POST', body: JSON.stringify({ habit_id: id, date: apiDate() }) });
    await loadHabits();
    showToast(completed ? 'Checked off for later.' : 'Habit logged. Keep going.');
  } catch (error) { showToast(error.message); }
}

async function archiveHabit(id) {
  try { await api(`/api/habits/${id}/archive`, { method: 'PATCH' }); await loadHabits(); showToast('Habit moved to archived.'); }
  catch (error) { showToast(error.message); }
}

function showToast(message) { const toast = $('#toast'); toast.textContent = message; toast.classList.add('show'); window.clearTimeout(showToast.timer); showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 2800); }
function openModal() { $('#modalBackdrop').classList.remove('hidden'); if (!state.editingHabitId) $('#habitForm').elements.start_date.value = apiDate(); $('#habitForm').elements.name.focus(); }
function closeModal() { $('#modalBackdrop').classList.add('hidden'); $('#habitForm').reset(); $('#weekdayPicker').classList.add('hidden'); $('#formError').textContent = ''; state.editingHabitId = null; $('#modalTitle').textContent = 'Add a habit'; }

$('#previousDay').addEventListener('click', () => { state.date.setDate(state.date.getDate() - 1); state.archived = false; loadHabits(); });
$('#nextDay').addEventListener('click', () => { state.date.setDate(state.date.getDate() + 1); state.archived = false; loadHabits(); });
$('#todayButton').addEventListener('click', () => { state.date = new Date(); state.archived = false; loadHabits(); });
$('#addHabitButton').addEventListener('click', openModal);
$('#emptyAction').addEventListener('click', openModal);
$('#manageAddButton').addEventListener('click', openModal);
$('#closeModal').addEventListener('click', closeModal);
$('#modalBackdrop').addEventListener('click', (event) => { if (event.target.id === 'modalBackdrop') closeModal(); });
$('#mobileMenu').addEventListener('click', () => $('.sidebar').classList.toggle('open'));
$('#logoutButton').addEventListener('click', logout);
$('#loginForm').addEventListener('submit', (event) => login(event).catch((error) => { $('#loginError').textContent = error.message; }));
$('#signupForm').addEventListener('submit', (event) => signup(event));
document.querySelectorAll('[data-auth-mode]').forEach((button) => button.addEventListener('click', () => setAuthMode(button.dataset.authMode)));
document.querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => setView(button.dataset.view)));
document.querySelectorAll('[data-manage-filter]').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('[data-manage-filter]').forEach((item) => item.classList.remove('active')); button.classList.add('active'); loadManageHabits(); }));
$('#habitSearch').addEventListener('input', () => loadManageHabits());

$('#manageList').addEventListener('click', async (event) => {
  const edit = event.target.closest('[data-edit]');
  const archive = event.target.closest('[data-toggle-archive]');
  if (edit) { await editHabit(Number(edit.dataset.edit)); return; }
  if (archive) {
    const isArchived = Boolean(document.querySelector('[data-manage-filter="archived"].active'));
    await api(`/api/habits/${archive.dataset.toggleArchive}/${isArchived ? 'restore' : 'archive'}`, { method: 'PATCH' });
    loadManageHabits();
  }
});

document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.filter').forEach((item) => item.classList.remove('active')); button.classList.add('active'); state.filter = button.dataset.filter; render(); }));
$('#habitList').addEventListener('click', (event) => { const complete = event.target.closest('[data-complete]'); const archive = event.target.closest('[data-archive]'); if (complete) { const habit = state.habits.find((item) => item.id === Number(complete.dataset.complete)); toggleCompletion(habit.id, habit.completed); } if (archive) archiveHabit(Number(archive.dataset.archive)); });
document.querySelectorAll('input[name="frequency_type"]').forEach((input) => input.addEventListener('change', (event) => $('#weekdayPicker').classList.toggle('hidden', event.target.value !== 'custom')));

$('#habitForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const form = new FormData(event.target); const frequency = form.get('frequency_type'); const days = [...document.querySelectorAll('#weekdayPicker input:checked')].map((input) => Number(input.value));
  if (frequency === 'custom' && !days.length) { $('#formError').textContent = 'Choose at least one day.'; return; }
  const payload = { name: form.get('name'), description: form.get('description') || null, start_date: form.get('start_date'), end_date: form.get('end_date') || null, frequency_type: frequency, days_of_week: frequency === 'custom' ? days : null };
  try {
    const editing = state.editingHabitId;
    await api(editing ? `/api/habits/${editing}` : '/api/habits', { method: editing ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    closeModal(); state.date = new Date(payload.start_date + 'T12:00:00'); state.archived = false;
    if (state.view === 'manage') loadManageHabits(); else { setView('today'); await loadHabits(); }
    showToast(editing ? 'Habit updated.' : 'A new habit joined your rhythm.');
  }
  catch (error) { $('#formError').textContent = error.message; }
});

function boot() {
  lucide.createIcons();
  if (state.user) enterApp(state.user);
  else { $('.app-shell').classList.add('hidden'); $('#authScreen').classList.remove('hidden'); setAuthMode('login'); }
}

boot();
