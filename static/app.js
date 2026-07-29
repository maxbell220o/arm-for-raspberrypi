async function post(path) {
  const response = await fetch(path, { method: 'POST' });
  if (!response.ok) alert(JSON.stringify(await response.json()));
  await refresh();
}

function driveCard(drive) {
  return `<article class="drive">
    <h2>${drive.id} — ${drive.vendor || ''} ${drive.model || ''}</h2>
    <p><strong>Gerät:</strong> ${drive.device}</p>
    <p><strong>Status:</strong> ${drive.status || 'unbekannt'}</p>
    <p><strong>Fortschritt:</strong> ${drive.progress || 0}%</p>
    <button onclick="post('/api/drives/${drive.id}/open')">Öffnen</button>
    <button onclick="post('/api/drives/${drive.id}/close')">Schließen</button>
    <button onclick="post('/api/drives/${drive.id}/rip')">Rippen starten</button>
  </article>`;
}

async function refresh() {
  const status = await fetch('/api/status').then((r) => r.json());
  const drives = Object.values(status.drives || {});
  document.querySelector('#drives').innerHTML = drives.length
    ? drives.map(driveCard).join('')
    : '<p>Keine optischen Laufwerke gefunden.</p>';
  document.querySelector('#jobs').textContent = JSON.stringify(status.jobs || [], null, 2);
}

refresh();
setInterval(refresh, 3000);
