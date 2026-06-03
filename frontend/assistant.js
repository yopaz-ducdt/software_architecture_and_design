const AI_API = 'http://localhost:8012';

function aiEscape(str) {
  return String(str || '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
}

async function aiReq(path, body) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(`${AI_API}${path}`, {
    method: body ? 'POST' : 'GET',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = 'AI request failed';
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

function appendAiMessage(role, text, topProducts = []) {
  const box = document.getElementById('ai-messages');
  if (!box) return;

  const div = document.createElement('div');
  div.className = `ai-message ${role}`;

  let inner = `<div class="ai-bubble">${aiEscape(text).replace(/\n/g, '<br>')}</div>`;

  if (role === 'bot' && topProducts && topProducts.length) {
    inner += '<div class="ai-products">' + topProducts.map((b) => `
      <div class="ai-product-card">
        <div class="ai-product-title">${aiEscape(b.title)}</div>
        <div class="ai-product-price">${Number(b.price || 0).toLocaleString('vi-VN')}đ</div>
        <div class="ai-product-desc">${aiEscape(b.description || 'Sản phẩm đang có trong catalog hiện tại.')}</div>
      </div>
    `).join('') + '</div>';
  }

  div.innerHTML = inner;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function setAiLoading(loading) {
  const btn = document.getElementById('ai-submit');
  const input = document.getElementById('ai-input');
  if (btn) btn.disabled = loading;
  if (input) input.disabled = loading;
  if (btn) btn.textContent = loading ? 'Đang gửi...' : 'Gửi';
}

async function askAssistant(question) {
  appendAiMessage('user', question);
  appendAiMessage('bot', 'Mình đang tìm sản phẩm và thông tin phù hợp cho bạn...');
  const msgs = document.getElementById('ai-messages');
  const loadingNode = msgs.lastElementChild;

  try {
    const res = await aiReq('/chat/ask', { question });
    if (loadingNode) loadingNode.remove();
    appendAiMessage('bot', res.answer, res.top_products || res.top_books || []);
  } catch (err) {
    if (loadingNode) loadingNode.remove();
    appendAiMessage('bot', err.message || 'Không thể gọi AI chatbot lúc này.');
  }
}

function openAiPopup() {
  const userRaw = localStorage.getItem('user');
  const token = localStorage.getItem('token');
  if (!userRaw || !token) {
    if (typeof toast === 'function') toast('Vui lòng đăng nhập để dùng AI chatbot', 'error');
    window.location.hash = '#/login';
    return;
  }
  const shell = document.getElementById('ai-popup-shell');
  if (!shell) return;
  shell.classList.remove('hidden');
  shell.classList.add('open');
  const input = document.getElementById('ai-input');
  if (input) setTimeout(() => input.focus(), 60);
}

function closeAiPopup() {
  const shell = document.getElementById('ai-popup-shell');
  if (!shell) return;
  shell.classList.add('hidden');
  shell.classList.remove('open');
}

function toggleAiPopup() {
  const shell = document.getElementById('ai-popup-shell');
  if (!shell) return;
  if (shell.classList.contains('hidden')) openAiPopup();
  else closeAiPopup();
}

function injectAiPopup() {
  if (document.getElementById('ai-floating-btn')) return;

  const html = `
    <button id="ai-floating-btn" class="ai-floating-btn" type="button" title="Mở AI tư vấn">
      <span class="ai-floating-icon">🤖</span>
      <span>AI tư vấn</span>
    </button>

    <div id="ai-popup-shell" class="ai-popup-shell hidden" aria-hidden="true">
      <section class="ai-popup-card">
        <header class="ai-popup-head">
          <div>
            <div class="ai-popup-title">AI tư vấn LearnMart</div>
            <div class="ai-popup-subtitle">Hỏi về sản phẩm, ngân sách, coupon, đổi trả, giao hàng.</div>
          </div>
          <div class="ai-popup-actions">
            <button id="ai-minimize-btn" class="ai-icon-btn" type="button" title="Thu nhỏ">—</button>
            <button id="ai-close-btn" class="ai-icon-btn" type="button" title="Đóng">✕</button>
          </div>
        </header>

        <div id="ai-messages" class="ai-messages">
          <div class="ai-message bot">
            <div class="ai-bubble">Xin chào 👋 Mình có thể gợi ý sản phẩm theo ngân sách, danh mục và giải thích coupon, thành viên, giao hàng hoặc đổi trả.</div>
          </div>
        </div>

        <div class="ai-suggestions">
          <button class="ai-suggestion-btn" data-q="Dưới 100k nên mua sản phẩm nào cho người mới đọc?">Dưới 100k</button>
          <button class="ai-suggestion-btn" data-q="Tôi thích sách self-help, tầm 120k nên chọn sản phẩm nào và vì sao?">Self-help 120k</button>
          <button class="ai-suggestion-btn" data-q="Tôi có nên dùng coupon hay lên hạng thành viên không?">Coupon / tier</button>
          <button class="ai-suggestion-btn" data-q="Phí ship và đổi trả bên mình thế nào?">Ship & đổi trả</button>
        </div>

        <form id="ai-form" class="ai-form">
          <input id="ai-input" class="ai-input" placeholder="Ví dụ: từ 80k đến 120k nên mua sản phẩm nào và vì sao?" />
          <button id="ai-submit" class="ai-submit" type="submit">Gửi</button>
        </form>
      </section>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', html);

  document.getElementById('ai-floating-btn').addEventListener('click', toggleAiPopup);
  document.getElementById('ai-close-btn').addEventListener('click', closeAiPopup);
  document.getElementById('ai-minimize-btn').addEventListener('click', closeAiPopup);

  document.getElementById('ai-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('ai-input');
    const q = input.value.trim();
    if (!q) return;
    input.value = '';
    setAiLoading(true);
    await askAssistant(q);
    setAiLoading(false);
  });

  document.querySelectorAll('.ai-suggestion-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      openAiPopup();
      setAiLoading(true);
      await askAssistant(btn.dataset.q || '');
      setAiLoading(false);
    });
  });

  const navAi = document.getElementById('nav-ai');
  if (navAi) {
    navAi.addEventListener('click', (e) => {
      e.preventDefault();
      openAiPopup();
    });
  }
}

window.addEventListener('load', () => {
  injectAiPopup();
});
