import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import router
from app.bot.telegram_bot import run_bot_in_background
from app.config import settings
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Ma'lumotlar bazasi tayyor")
    bot_task = run_bot_in_background()
    yield
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Maktab Davomat Tizimi",
    description="Tirniket integratsiyasi va ota-onalarga Telegram orqali xabar berish",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/admin", response_class=HTMLResponse)
def admin_panel() -> str:
    return """
<!doctype html>
<html lang="uz">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Maktab davomat admin</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f6f7fb; color: #18212f; }
    .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 18px; box-shadow: 0 2px 12px #0001; }
    input, button { padding: 10px; margin: 4px 0; border-radius: 8px; border: 1px solid #ccd3df; }
    button { background: #2563eb; color: white; border: 0; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; background: white; }
    th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e5e7eb; }
    .active { color: #047857; font-weight: bold; }
    .inactive { color: #b91c1c; font-weight: bold; }
    .muted { color: #667085; }
  </style>
</head>
<body>
  <h1>Maktab davomat admin paneli</h1>
  <div class="card">
    <label>Admin API kalit</label><br />
    <input id="adminKey" type="password" placeholder="ADMIN_API_KEY" style="width: 320px;" />
    <button onclick="saveKey()">Saqlash</button>
    <button onclick="loadParents()">Yangilash</button>
  </div>

  <div class="card">
    <h2>To'lov kiritish</h2>
    <input id="telegramId" placeholder="Telegram ID" />
    <input id="parentId" placeholder="yoki Parent ID" />
    <input id="months" type="number" min="1" value="1" />
    <input id="amount" type="number" placeholder="Summa (so'm)" />
    <input id="note" placeholder="Izoh" />
    <button onclick="createPayment()">Obunani faollashtirish</button>
    <p class="muted">Telegram ID ni ota-onalar jadvalidan oling. Parent ID kiritilsa Telegram ID shart emas.</p>
  </div>

  <div class="card">
    <h2>Ota-onalar</h2>
    <div id="message" class="muted"></div>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Telegram ID</th>
          <th>Ism</th>
          <th>Farzandlar</th>
          <th>Obuna</th>
          <th>Muddati</th>
        </tr>
      </thead>
      <tbody id="parents"></tbody>
    </table>
  </div>

  <script>
    const keyInput = document.getElementById('adminKey');
    keyInput.value = localStorage.getItem('adminKey') || '';

    function saveKey() {
      localStorage.setItem('adminKey', keyInput.value);
      loadParents();
    }

    function headers() {
      return { 'X-Admin-Key': keyInput.value, 'Content-Type': 'application/json' };
    }

    function formatDate(value) {
      if (!value) return '-';
      return new Date(value).toLocaleDateString('uz-UZ');
    }

    async function loadParents() {
      const message = document.getElementById('message');
      const body = document.getElementById('parents');
      message.textContent = 'Yuklanmoqda...';
      try {
        const res = await fetch('/api/admin/parents', { headers: headers() });
        if (!res.ok) throw new Error(await res.text());
        const parents = await res.json();
        body.innerHTML = parents.map(parent => `
          <tr>
            <td>${parent.id}</td>
            <td>${parent.telegram_id}</td>
            <td>${parent.full_name || '-'}</td>
            <td>${parent.children.map(child => `${child.full_name} (${child.class_name})`).join('<br>') || '-'}</td>
            <td class="${parent.subscription_active ? 'active' : 'inactive'}">
              ${parent.subscription_active ? 'Faol' : 'Faol emas'}
            </td>
            <td>${formatDate(parent.subscription_expires_at)}</td>
          </tr>
        `).join('');
        message.textContent = `${parents.length} ta ota-ona topildi.`;
      } catch (error) {
        message.textContent = 'Xato: ' + error.message;
      }
    }

    async function createPayment() {
      const payload = {
        months: Number(document.getElementById('months').value || 1),
        note: document.getElementById('note').value || null,
      };
      const parentId = document.getElementById('parentId').value;
      const telegramId = document.getElementById('telegramId').value;
      const amount = document.getElementById('amount').value;
      if (parentId) payload.parent_id = Number(parentId);
      if (telegramId) payload.telegram_id = Number(telegramId);
      if (amount) payload.amount_som = Number(amount);

      const res = await fetch('/api/admin/payments', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        alert('Xato: ' + await res.text());
        return;
      }
      alert('To\\'lov saqlandi va obuna faollashtirildi.');
      loadParents();
    }

    if (keyInput.value) loadParents();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
