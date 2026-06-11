// ══════════════════════════════════════════════
//  app.js  –  BookStore SPA  (hash router)
// ══════════════════════════════════════════════

// ── State ──────────────────────────────────────
const state = { user: null, cartCount: 0 };

function loadState() {
  const raw = localStorage.getItem('user');
  if (raw) state.user = JSON.parse(raw);
  updateNavUI();
  refreshCartBadge();
}
function saveUser(u) { state.user = u; localStorage.setItem('user', JSON.stringify(u)); }
function logout() {
  state.user = null; localStorage.removeItem('user'); localStorage.removeItem('token');
  updateNavUI(); toast('Đã đăng xuất', 'info'); navigate('/');
}

// ── Toast ──────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icon}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Modal ──────────────────────────────────────
function openModal(html) {
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-overlay').classList.remove('hidden');
}
function closeModal() { document.getElementById('modal-overlay').classList.add('hidden'); }
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', e => { if (e.target.id === 'modal-overlay') closeModal(); });

// ── Loader ─────────────────────────────────────
function loading() { return '<div class="loader"><div class="spinner"></div><p>Đang tải...</p></div>'; }

// ── Format ─────────────────────────────────────
function fmt(n) { return Number(n || 0).toLocaleString('vi') + 'đ'; }
function stars(r) { return '★'.repeat(Math.round(r || 0)) + '☆'.repeat(5 - Math.round(r || 0)); }
function statusClass(s) {
  const m = { PENDING: 'pending', PROCESSING: 'processing', SHIPPED: 'shipped', DELIVERED: 'delivered', CANCELLED: 'cancelled' };
  return 'status-' + (m[s] || 'pending');
}

function trackBehavior(event) {
  if (!state.user || state.user.user_type !== 'customer') return;
  Behavior.track({ customer_id: state.user.user_id, ...event }).catch(() => { });
}

// ── Nav UI ─────────────────────────────────────
function updateNavUI() {
  const u = state.user;
  const loggedIn = !!u;
  document.getElementById('nav-login').classList.toggle('hidden', loggedIn);
  document.getElementById('nav-register').classList.toggle('hidden', loggedIn);
  document.getElementById('nav-user').classList.toggle('hidden', !loggedIn);
  document.getElementById('nav-wishlist').classList.toggle('hidden', !loggedIn || u?.user_type !== 'customer');
  document.getElementById('nav-staff').classList.toggle('hidden', !loggedIn || u?.user_type !== 'staff');
  if (u) {
    document.getElementById('user-menu-btn').textContent = (u.name || '?').charAt(0).toUpperCase();
    document.getElementById('user-info-box').innerHTML =
      `<div class="uname">${u.name}</div><div class="utype">${u.user_type === 'staff' ? '👔 Nhân viên' : '👤 Khách hàng'}</div>`;
  }
}

async function refreshCartBadge() {
  if (!state.user || state.user.user_type !== 'customer') return;
  try {
    const s = await Order.cartSummary(state.user.user_id);
    const cnt = s.item_count || 0;
    document.getElementById('cart-badge').textContent = cnt;
    state.cartCount = cnt;
  } catch { }
}

// ── Router ─────────────────────────────────────
const app = document.getElementById('app');
const routes = {
  '/': renderHome,
  '/products': renderProducts,
  '/product': renderProductDetail,
  '/cart': renderCart,
  '/checkout': renderCheckout,
  '/login': renderLogin,
  '/register': renderRegister,
  '/profile': renderProfile,
  '/orders': renderOrders,
  '/wishlist': renderWishlist,
  '/staff': renderStaffDashboard,
  '/marketing': renderMarketing,
  '/notifications': renderNotifications,
};

function navigate(path) { window.location.hash = '#' + path; }

window.addEventListener('hashchange', route);
window.addEventListener('load', () => { loadState(); route(); });

function route() {
  // hash is e.g. '/products' or '/product/5' or '/'
  const hash = window.location.hash.replace('#', '') || '/';
  const segments = hash.split('/').filter(s => s !== '');   // ['products'] or ['product','5'] or []
  const path = segments[0] || '';                            // 'products' | 'product' | ''
  const param = segments[1] || undefined;                    // '5' | undefined
  const key = '/' + path;                                    // '/products' | '/product' | '/'

  const fn = routes[key];
  // Set active nav
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelectorAll(`.nav-link[href="#${key}"]`).forEach(l => l.classList.add('active'));
  if (fn) fn(param);
  else { app.innerHTML = '<div class="empty"><h3>404 – Không tìm thấy trang</h3><a href="#/" class="btn btn-primary mt-3">Về trang chủ</a></div>'; }
}

// ═══════════════════════════════════════════════
//  PAGES
// ═══════════════════════════════════════════════

// ── HOME ───────────────────────────────────────
async function renderHome() {
  app.innerHTML = loading();
  const shouldLoadRecommendations = state.user?.user_type === 'customer';
  const [productsRes, flashSales, promos] = await Promise.allSettled([
    Product.list('', '', '', 0, 8),
    Marketing.flashSales(),
    Marketing.promotions(),
  ]);
  const productList = productsRes.value || [];
  const sales = (flashSales.value || []).slice(0, 3);
  const promoList = (promos.value || []).slice(0, 3);

  app.innerHTML = `
    <div class="hero">
      <div class="hero-content">
        <h1>Khám phá <span>LearnMart</span><br/>Tuyệt Vời Nhất</h1>
        <p>Catalog học tập và quà tặng với 10 nhóm sản phẩm từ sách đến phụ kiện bàn học.</p>
        <div class="hero-actions">
          <a href="#/products" class="btn btn-primary btn-lg">🔍 Xem tất cả sản phẩm</a>
          ${!state.user ? '<a href="#/register" class="btn btn-outline btn-lg">Đăng ký miễn phí</a>' : ''}
        </div>
      </div>
      <div class="hero-float">
        <div class="hero-stat"><div class="num">500+</div><div class="label">Sản phẩm</div></div>
      <div class="hero-stat"><div class="num">10</div><div class="label">Nhóm sản phẩm</div></div>
        <div class="hero-stat"><div class="num">24h</div><div class="label">Giao hàng</div></div>
        <div class="hero-stat"><div class="num">4.9★</div><div class="label">Đánh giá</div></div>
      </div>
    </div>

    ${sales.length ? `
    <div class="mb-4">
      <div class="section-header"><h2 class="section-title">⚡ <span>Flash Sale</span></h2></div>
      <div class="grid-3">
        ${sales.map(s => `
          <div class="flash-sale-card">
            <div class="tag tag-purple mb-2">-${s.discount_percent}% OFF</div>
            <h3 class="fw-bold">${s.name}</h3>
            <div class="text-muted" style="font-size:.8rem;margin-top:.5rem">
              Đến: ${new Date(s.end_at).toLocaleString('vi')}
            </div>
          </div>`).join('')}
      </div>
    </div>` : ''}

    <div class="mb-4">
      <div class="section-header">
        <h2 class="section-title">📚 <span>Sản phẩm mới</span></h2>
        <a href="#/products" class="btn btn-ghost btn-sm">Xem tất cả →</a>
      </div>
      <div class="grid-4">
        ${productList.map(productCard).join('')}
      </div>
    </div>

    <div class="mb-4">
      <div class="section-header">
        <h2 class="section-title">✨ <span>Gợi ý cho bạn</span></h2>
      </div>
      <div id="home-recommendations">
        ${shouldLoadRecommendations ? '<div class="text-muted" style="font-size:.9rem">Đang tải gợi ý cá nhân hóa...</div>' : '<div class="text-muted" style="font-size:.9rem">Đăng nhập để nhận gợi ý phù hợp hơn.</div>'}
      </div>
    </div>

    ${promoList.length ? `
    <div class="mb-4">
      <div class="section-header"><h2 class="section-title">🎁 <span>Khuyến Mãi</span></h2></div>
      <div class="grid-3">
        ${promoList.map(p => `
          <div class="card" style="padding:1.25rem">
            <div class="tag mb-2">${p.discount_percent ? `-${p.discount_percent}%` : 'Hot'}</div>
            <h3 class="fw-bold mb-1">${p.name}</h3>
            <p class="text-muted" style="font-size:.85rem">${p.description || ''}</p>
          </div>`).join('')}
      </div>
    </div>` : ''}
  `;

  // Attach product click handlers
  document.querySelectorAll('.book-card').forEach(c => {
    c.addEventListener('click', () => {
      trackBehavior({ event_type: 'product_clicked_from_listing', product_id: parseInt(c.dataset.id), source: 'frontend_home' });
      navigate(`/product/${c.dataset.id}`);
    });
  });
  document.querySelectorAll('.add-cart-btn').forEach(b => {
    b.addEventListener('click', e => { e.stopPropagation(); addToCart(b.dataset.id, b.dataset.price); });
  });

  if (shouldLoadRecommendations) {
    AI.recommendations(4)
      .then((recommendBlock) => {
        const container = document.getElementById('home-recommendations');
        if (!container) return;
        if (!recommendBlock?.products?.length) {
          container.innerHTML = '<div class="text-muted" style="font-size:.9rem">Chưa có đủ dữ liệu để gợi ý cá nhân hóa.</div>';
          return;
        }
        container.innerHTML = `
          <p class="text-muted mb-2" style="font-size:.9rem">${recommendBlock.summary || ''}</p>
          <div class="grid-4">
            ${recommendBlock.products.map(productCard).join('')}
          </div>
        `;
        container.querySelectorAll('.book-card').forEach(c => {
          c.addEventListener('click', () => {
            trackBehavior({ event_type: 'product_clicked_from_listing', product_id: parseInt(c.dataset.id), source: 'frontend_recommendation' });
            navigate(`/product/${c.dataset.id}`);
          });
        });
        container.querySelectorAll('.add-cart-btn').forEach(b => {
          b.addEventListener('click', e => { e.stopPropagation(); addToCart(b.dataset.id, b.dataset.price); });
        });
      })
      .catch(() => {
        const container = document.getElementById('home-recommendations');
        if (!container) return;
        container.innerHTML = '<div class="text-muted" style="font-size:.9rem">Tạm thời chưa tải được gợi ý cá nhân hóa.</div>';
      });
  }
}

function productCard(b) {
  const price = fmt(b.price);
  const imageUrl = b.image_url || b.cover_image_url || `https://picsum.photos/seed/${encodeURIComponent(b.sku || b.id)}/400/600`;
  return `
    <div class="card book-card" data-id="${b.id}">
      <div class="book-cover">
        <img src="${imageUrl}" alt="${b.title}">
        ${(b.stock_quantity || 0) < 10 ? '<span class="book-badge">Sắp hết</span>' : ''}
      </div>
      <div class="book-info">
        <div class="book-title">${b.title}</div>
        <div class="book-author">${b.author_name || '—'}</div>
        <div class="book-price">${price}</div>
        <div class="book-rating">${stars(b.rating_avg)} <span style="color:var(--text2)">(${b.rating_count || 0})</span></div>
      </div>
      <div class="book-actions">
        <button class="btn btn-primary btn-sm w-full add-cart-btn" data-id="${b.id}" data-price="${b.price}">🛒 Thêm giỏ</button>
      </div>
    </div>`;
}

function bindProductCardEvents(root = document) {
  root.querySelectorAll('.book-card').forEach(c => {
    c.addEventListener('click', () => {
      trackBehavior({ event_type: 'product_clicked_from_listing', product_id: parseInt(c.dataset.id), source: 'frontend_listing' });
      navigate(`/product/${c.dataset.id}`);
    });
  });
  root.querySelectorAll('.add-cart-btn').forEach(b => {
    b.addEventListener('click', e => { e.stopPropagation(); addToCart(b.dataset.id, b.dataset.price); });
  });
}

function renderAiRecommendationSection(targetId, title, response) {
  const el = document.getElementById(targetId);
  if (!el) return;
  const products = response?.top_products || response?.products || [];
  const summary = response?.answer || response?.summary || '';
  if (!products.length) {
    el.innerHTML = `<div class="text-muted" style="font-size:.9rem">AI chưa tìm thấy gợi ý phù hợp hơn ở thời điểm này.</div>`;
    return;
  }
  el.innerHTML = `
    <div class="card" style="padding:1rem 1.25rem;margin-top:1rem">
      <div class="section-header" style="margin-bottom:.75rem">
        <h3 class="section-title" style="font-size:1.05rem">🤖 <span>${title}</span></h3>
      </div>
      <p class="text-muted mb-2" style="font-size:.9rem">${summary}</p>
      <div class="grid-4">
        ${products.map(productCard).join('')}
      </div>
    </div>`;
  bindProductCardEvents(el);
}

async function addToCart(productId, price) {
  if (!state.user || state.user.user_type !== 'customer') {
    toast('Vui lòng đăng nhập để mua hàng', 'error'); navigate('/login'); return;
  }
  try {
    await Order.addToCart(state.user.user_id, { product_id: parseInt(productId), quantity: 1, unit_price: parseFloat(price) || 0 });
    trackBehavior({ event_type: 'cart_added', product_id: parseInt(productId), price: parseFloat(price) || 0, quantity: 1, source: 'frontend' });
    toast('Đã thêm vào giỏ hàng!', 'success');
    refreshCartBadge();
    if (state.user?.user_type === 'customer') {
      AI.ask('Tôi vừa thêm sản phẩm vào giỏ, hãy gợi ý 3 sản phẩm liên quan để upsell hoặc bundle.').then(res => {
        renderAiRecommendationSection('cart-ai-slot', 'Gợi ý thêm sau khi vào giỏ', res);
      }).catch(() => {});
    }
  } catch (e) { toast(e.message, 'error'); }
}

// ── PRODUCT LIST ───────────────────────────────
async function renderProducts() {
  app.innerHTML = loading();

  // Fetch tất cả song song một lần duy nhất
  const [categoriesRes, productsRes] = await Promise.allSettled([
    Product.categories(),
    Product.list('', '', '', 0, 40),
  ]);
  const categories = categoriesRes.value || [];
  let products = productsRes.value || [];

  let search = '', categoryId = '';

  const renderGrid = (productList) => {
    document.getElementById('product-grid').innerHTML = productList.length
      ? productList.map(productCard).join('')
      : '<div class="empty"><p>Không tìm thấy sản phẩm nào phù hợp.</p></div>';
    bindProductCardEvents(document.getElementById('product-grid'));
  };

  const refetch = async () => {
    document.getElementById('product-grid').innerHTML = '<div class="loader"><div class="spinner"></div></div>';
    const productsRes2 = await Product.list(search, categoryId, '', 0, 40).catch(() => []);
    if (search.trim()) trackBehavior({ event_type: 'search_performed', query: search.trim(), source: 'frontend' });
    renderGrid(productsRes2 || []);
    const aiSlot = document.getElementById('search-ai-slot');
    if (aiSlot) aiSlot.innerHTML = '';
    if (search.trim() && state.user?.user_type === 'customer') {
      AI.ask(`Khách hàng vừa tìm kiếm: ${search.trim()}. Hãy gợi ý 3 sản phẩm phù hợp nhất.`)
        .then(res => renderAiRecommendationSection('search-ai-slot', 'AI gợi ý theo từ khóa tìm kiếm', res))
        .catch(() => {});
    }
  };

  app.innerHTML = `
    <div class="section-header mb-3"><h1 class="section-title">🛍️ <span>Kho sản phẩm</span></h1></div>
    <div class="search-bar">
      <input class="form-input" id="search-inp" placeholder="Tìm kiếm theo tên sản phẩm..." />
      <button class="btn btn-primary" id="search-btn">🔍 Tìm</button>
    </div>
    <div class="filter-bar">
      <select class="form-input" id="filter-category">
        <option value="">Tất cả danh mục</option>
        ${categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
      </select>
    </div>
    <div id="product-grid" class="grid-4"></div>
    <div id="search-ai-slot"></div>`;

  // Hiển thị sản phẩm ngay lập tức từ data đã fetch
  renderGrid(products);

  document.getElementById('search-btn').onclick = () => { search = document.getElementById('search-inp').value; refetch(); };
  document.getElementById('search-inp').onkeydown = e => { if (e.key === 'Enter') { search = e.target.value; refetch(); } };
  document.getElementById('filter-category').onchange = e => { categoryId = e.target.value; refetch(); };
}

// ── PRODUCT DETAIL ─────────────────────────────
async function renderProductDetail(id) {
  if (!id) { navigate('/products'); return; }
  app.innerHTML = loading();
  const [productRes, reviewsRes, ratingsRes] = await Promise.allSettled([
    Product.get(id), Product.getReviews(id), Product.getRatings(id)
  ]);
  const b = productRes.value;
  if (!b) { app.innerHTML = '<div class="empty"><h3>Không tìm thấy sản phẩm</h3></div>'; return; }
  const reviews = Array.isArray(reviewsRes.value) ? reviewsRes.value : [];
  const ratings = Array.isArray(ratingsRes.value) ? ratingsRes.value : [];
  const avgRating = ratings.length ? (ratings.reduce((a, r) => a + r.score, 0) / ratings.length).toFixed(1) : 0;

  if (state.user?.user_type === 'customer')
    Analytics.logView({ customer_id: state.user.user_id, product_id: parseInt(id) }).catch(() => { });
  if (state.user?.user_type === 'customer')
    trackBehavior({ event_type: 'product_viewed', product_id: parseInt(id), category_name: b.category_name, price: parseFloat(b.price) || 0, source: 'frontend' });

  app.innerHTML = `
    <button class="btn btn-ghost btn-sm mb-3" onclick="history.back()">← Quay lại</button>
    <div style="display:grid;grid-template-columns:280px 1fr;gap:2.5rem;align-items:start">
      <div>
        <div class="book-cover" style="border-radius:var(--radius);aspect-ratio:2/3;font-size:5rem">
          <img src="${b.image_url || b.cover_image_url || `https://picsum.photos/seed/${encodeURIComponent(b.sku || b.id)}/400/600`}" alt="${b.title}">
        </div>
        <button class="btn btn-primary w-full mt-3" id="add-btn">🛒 Thêm vào giỏ</button>
        <button class="btn btn-ghost w-full mt-2" id="wish-btn">❤️ Wishlist</button>
      </div>
      <div>
        <h1 style="font-size:1.8rem;font-weight:900;margin-bottom:.5rem">${b.title}</h1>
        <p class="text-muted mb-2">by <strong>${b.author_name || '—'}</strong></p>
        <div class="flex gap-1 mb-3">
          ${b.genre_name ? `<span class="tag">${b.genre_name}</span>` : ''}
          ${b.language ? `<span class="tag tag-cyan">${b.language}</span>` : ''}
          ${(b.stock_quantity || 0) < 1 ? '<span class="tag tag-red">Hết hàng</span>' : `<span class="tag tag-green">Còn ${b.stock_quantity || 0}</span>`}
        </div>
        <div style="font-size:2rem;font-weight:900;color:var(--indigo);margin-bottom:1rem">${fmt(b.price)}</div>
        <div class="text-muted mb-3">${b.description || 'Chưa có mô tả.'}</div>
        <div class="card" style="padding:1rem;margin-bottom:1.5rem">
          <div class="flex gap-2 mb-2">
            <span style="font-size:2rem;font-weight:900;color:var(--yellow)">${avgRating}</span>
            <div><div class="stars">${stars(avgRating)}</div><div class="text-muted" style="font-size:.8rem">${ratings.length} đánh giá</div></div>
          </div>
        </div>
        ${state.user?.user_type === 'customer' ? `
        <div class="card" style="padding:1.25rem;margin-bottom:1.5rem">
          <h3 class="fw-bold mb-2">Viết đánh giá</h3>
          <div class="rating-input mb-2" id="star-input">
            ${[1, 2, 3, 4, 5].map(i => `<span data-v="${i}">☆</span>`).join('')}
          </div>
          <textarea class="form-input mb-2" id="review-body" placeholder="Chia sẻ cảm nhận của bạn..."></textarea>
          <button class="btn btn-primary" id="submit-review">Gửi đánh giá</button>
        </div>` : ''}
        <h3 class="fw-bold mb-2">Bình luận (${reviews.length})</h3>
        <div id="reviews-list">
          ${reviews.length ? reviews.map(r => `
            <div class="card" style="padding:1rem;margin-bottom:.75rem">
              <div class="flex" style="justify-content:space-between;margin-bottom:.4rem">
                <span class="fw-bold" style="font-size:.85rem">Khách #${r.customer_id}</span>
                <span class="text-muted" style="font-size:.75rem">${new Date(r.created_at).toLocaleDateString('vi')}</span>
              </div>
              <p style="font-size:.88rem">${r.body}</p>
            </div>`).join('') : '<p class="text-muted">Chưa có bình luận.</p>'}
        </div>
      </div>
    </div>`;

  document.getElementById('add-btn').onclick = () => addToCart(id, b.price);
  document.getElementById('wish-btn').onclick = async () => {
    if (!state.user) { navigate('/login'); return; }
    try {
      const r = await Customer.toggleWish(state.user.user_id, id);
      if (r.action === 'added') trackBehavior({ event_type: 'wishlist_added', product_id: parseInt(id), category_name: b.category_name, price: parseFloat(b.price) || 0, source: 'frontend' });
      toast(r.action === 'added' ? 'Đã thêm Wishlist!' : 'Đã xóa khỏi Wishlist', 'success');
    }
    catch (e) { toast(e.message, 'error'); }
  };
  // Star rating
  const starEl = document.getElementById('star-input');
  if (starEl) {
    let rating = 0;
    starEl.querySelectorAll('span').forEach(s => {
      s.onclick = () => {
        rating = parseInt(s.dataset.v);
        starEl.querySelectorAll('span').forEach((x, i) => x.textContent = i < rating ? '★' : '☆');
      };
    });
    document.getElementById('submit-review').onclick = async () => {
      const body = document.getElementById('review-body').value.trim();
      if (!body) { toast('Vui lòng nhập nội dung đánh giá', 'error'); return; }
      try {
        await Product.review({ product_id: parseInt(id), customer_id: state.user.user_id, body });
        if (rating) await Product.rate({ product_id: parseInt(id), customer_id: state.user.user_id, score: rating });
        toast('Đã gửi đánh giá!', 'success'); renderProductDetail(id);
      } catch (e) { toast(e.message, 'error'); }
    };
  }
}

// ── CART ───────────────────────────────────────
async function renderCart() {
  if (!state.user || state.user.user_type !== 'customer') { navigate('/login'); return; }
  app.innerHTML = loading();
  const cart = await Order.cart(state.user.user_id).catch(() => null);
  const items = cart?.items || [];
  // Fetch product details for cart items
  await Promise.all(items.map(async i => {
      if(!i.product_title) {
          const pid = i.product_id;
          const b = await Product.get(pid).catch(()=>null);
          i.product_title = b?.title || `Sản phẩm #${pid}`;
          i.author_name = b?.author_name || b?.category_name || 'LearnMart';
      }
  }));
  const total = items.reduce((s, i) => s + (i.unit_price || 0) * i.quantity, 0);
  const ship = 15000;

  app.innerHTML = `
    <h1 class="section-title mb-4">🛒 <span>Giỏ Hàng</span></h1>
    ${items.length ? `
      <div class="cart-layout">
        <div>
          ${items.map(i => `
            <div class="card cart-item mb-2" data-id="${i.id}">
              <div class="cart-item-icon">📖</div>
              <div class="cart-item-info">
                <div class="cart-item-title">${i.product_title}</div><div class="text-muted" style="font-size:0.8rem">${i.author_name}</div>
                <div class="cart-item-price">${fmt(i.unit_price)}</div>
              </div>
              <div class="qty-control">
                <button class="qty-btn dec-btn" data-id="${i.id}">−</button>
                <span style="min-width:28px;text-align:center;font-weight:700">${i.quantity}</span>
                <button class="qty-btn inc-btn" data-id="${i.id}" data-qty="${i.quantity}">+</button>
              </div>
              <button class="btn btn-danger btn-sm rm-btn" data-id="${i.id}">✕</button>
            </div>`).join('')}
          <button class="btn btn-ghost btn-sm mt-2" id="clear-btn">🗑 Xóa giỏ hàng</button>
        </div>
        <div class="summary-box">
          <h3 class="fw-bold mb-3">Tóm tắt đơn hàng</h3>
          <div class="summary-row"><span>Tạm tính</span><span>${fmt(total)}</span></div>
          <div class="summary-row"><span>Phí giao hàng</span><span>${fmt(ship)}</span></div>
          <div class="summary-row total"><span>Tổng cộng</span><span>${fmt(total + ship)}</span></div>
          <button class="btn btn-primary w-full mt-3" id="checkout-btn">Đặt hàng ngay →</button>
        </div>
      </div>
      <div id="cart-ai-slot"></div>` : `
      <div class="empty">
        <div style="font-size:4rem">🛒</div>
        <h3>Giỏ hàng trống</h3>
        <p>Hãy thêm sản phẩm vào giỏ để bắt đầu mua sắm</p>
        <a href="#/products" class="btn btn-primary">Khám phá sản phẩm</a>
      </div>`}`;

  const checkoutBtn = document.getElementById('checkout-btn');
  if (checkoutBtn) checkoutBtn.addEventListener('click', () => navigate('/checkout'));
  document.getElementById('clear-btn')?.addEventListener('click', async () => {
    await Order.clearCart(state.user.user_id); toast('Đã xóa giỏ hàng', 'info'); renderCart(); refreshCartBadge();
  });
  document.querySelectorAll('.rm-btn').forEach(b => b.addEventListener('click', async () => {
    await Order.removeItem(state.user.user_id, b.dataset.id); renderCart(); refreshCartBadge();
  }));

  document.querySelectorAll('.inc-btn').forEach(b => b.addEventListener('click', async () => {
    await Order.updateQty(state.user.user_id, b.dataset.id, parseInt(b.dataset.qty) + 1); renderCart();
  }));
  document.querySelectorAll('.dec-btn').forEach(b => b.addEventListener('click', async () => {
    const item = items.find(i => i.id == b.dataset.id);
    if (item?.quantity <= 1) await Order.removeItem(state.user.user_id, b.dataset.id);
    else await Order.updateQty(state.user.user_id, b.dataset.id, item.quantity - 1);
    renderCart(); refreshCartBadge();
  }));

  if (items.length) {
    AI.ask('Khách hàng đang xem giỏ hàng, hãy gợi ý 3 sản phẩm liên quan để cross-sell.').then(res => {
      renderAiRecommendationSection('cart-ai-slot', 'AI gợi ý thêm trong giỏ hàng', res);
    }).catch(() => {});
  }
}

// ── CHECKOUT ───────────────────────────────────
async function renderCheckout() {
  if (!state.user || state.user.user_type !== 'customer') { navigate('/login'); return; }
  const summary = await Order.cartSummary(state.user.user_id).catch(() => ({ item_count: 0, total_price: 0 }));
  if (!summary.item_count) { toast('Giỏ hàng trống', 'error'); navigate('/cart'); return; }

  app.innerHTML = `
    <h1 class="section-title mb-4">💳 <span>Thanh Toán</span></h1>
    <div style="display:grid;grid-template-columns:1fr 320px;gap:2rem">
      <form id="checkout-form">
        <div class="form-group">
          <label class="form-label">Phương thức giao hàng</label>
          <select class="form-input" name="ship_method">
            <option value="standard">Tiêu chuẩn (15.000đ)</option>
            <option value="fast">Nhanh (30.000đ)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Phương thức thanh toán</label>
          <select class="form-input" name="pay_method">
            <option value="COD">Thanh toán khi nhận hàng (COD)</option>
            <option value="BANKING">Chuyển khoản</option>
            <option value="MOMO">MoMo</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Mã giảm giá</label>
          <div class="flex gap-1">
            <input class="form-input" name="coupon_code" placeholder="Nhập mã coupon..." />
            <button type="button" class="btn btn-outline" id="apply-coupon">Áp dụng</button>
          </div>
          <div id="coupon-result" style="margin-top:.5rem;font-size:.85rem"></div>
        </div>
        <div class="form-group">
          <label class="form-label">Ghi chú</label>
          <textarea class="form-input" name="note" placeholder="Ghi chú cho đơn hàng..."></textarea>
        </div>
        <button type="submit" class="btn btn-primary btn-lg w-full">✓ Xác nhận đặt hàng</button>
      </form>
      <div class="summary-box">
        <h3 class="fw-bold mb-3">Tóm tắt</h3>
        <div class="summary-row"><span>Số sản phẩm</span><span>${summary.item_count}</span></div>
        <div class="summary-row"><span>Tạm tính</span><span>${fmt(summary.total_price)}</span></div>
        <div class="summary-row total" id="grand-total"><span>Tổng cộng</span><span>${fmt(summary.total_price + 15000)}</span></div>
      </div>
    </div>`;

  document.getElementById('apply-coupon').onclick = async () => {
    const code = document.querySelector('[name=coupon_code]').value.trim();
    if (!code) return;
    try {
      const r = await Marketing.validateCoupon(code, summary.total_price);
      document.getElementById('coupon-result').innerHTML = `<span class="text-green">✓ Tiết kiệm ${fmt(r.discount)}</span>`;
      toast('Mã hợp lệ!', 'success');
    } catch (e) { document.getElementById('coupon-result').innerHTML = `<span class="text-red">✕ ${e.message}</span>`; }
  };

  document.getElementById('checkout-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      customer_id: state.user.user_id,
      ship_method: fd.get('ship_method'),
      pay_method: fd.get('pay_method'),
      coupon_code: fd.get('coupon_code') || null,
      note: fd.get('note') || null,
    };
    try {
      const order = await Order.checkout(body);
      trackBehavior({ event_type: 'checkout_started', source: 'frontend', quantity: summary.item_count, price: summary.total_price });
      trackBehavior({ event_type: 'order_completed', source: 'frontend', quantity: summary.item_count, price: summary.total_price });
      toast('Đặt hàng thành công!', 'success');
      refreshCartBadge();
      navigate(`/orders`);
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── LOGIN ──────────────────────────────────────
function renderLogin() {
  app.innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <div class="auth-title">👋 Đăng nhập</div>
        <div class="auth-subtitle">Chào mừng quay lại LearnMart</div>
        <div class="tab-bar">
          <button class="tab-btn active" id="tab-customer">Khách hàng</button>
          <button class="tab-btn" id="tab-staff">Nhân viên</button>
        </div>
        <form id="login-form">
          <div id="customer-fields">
            <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email" placeholder="email@example.com" /></div>
          </div>
          <div id="staff-fields" class="hidden">
            <div class="form-group"><label class="form-label">Tên đăng nhập</label><input class="form-input" name="username" placeholder="username" /></div>
          </div>
          <div class="form-group"><label class="form-label">Mật khẩu</label><input class="form-input" name="password" type="password" placeholder="••••••••" /></div>
          <button type="submit" class="btn btn-primary w-full btn-lg">Đăng nhập</button>
          <p class="text-center mt-2 text-muted" style="font-size:.85rem">Chưa có tài khoản? <a href="#/register" class="link">Đăng ký</a></p>
        </form>
      </div>
    </div>`;

  let isStaff = false;
  document.getElementById('tab-customer').onclick = () => {
    isStaff = false;
    document.getElementById('tab-customer').classList.add('active');
    document.getElementById('tab-staff').classList.remove('active');
    document.getElementById('customer-fields').classList.remove('hidden');
    document.getElementById('staff-fields').classList.add('hidden');
  };
  document.getElementById('tab-staff').onclick = () => {
    isStaff = true;
    document.getElementById('tab-staff').classList.add('active');
    document.getElementById('tab-customer').classList.remove('active');
    document.getElementById('staff-fields').classList.remove('hidden');
    document.getElementById('customer-fields').classList.add('hidden');
  };
  document.getElementById('login-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      let res;
      if (isStaff) res = await Auth.loginStaff({ username: fd.get('username'), password: fd.get('password') });
      else res = await Auth.loginCustomer({ email: fd.get('email'), password: fd.get('password') });
      localStorage.setItem('token', res.access_token);
      saveUser({ user_id: res.user_id, name: res.name, user_type: res.user_type, role: res.role });
      toast(`Xin chào, ${res.name}!`, 'success');
      updateNavUI(); refreshCartBadge();
      navigate(res.user_type === 'staff' ? '/staff' : '/');
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── REGISTER ───────────────────────────────────
function renderRegister() {
  app.innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <div class="auth-title">✨ Đăng ký</div>
        <div class="auth-subtitle">Tạo tài khoản LearnMart miễn phí</div>
        <form id="reg-form">
          <div class="form-group"><label class="form-label">Họ và tên</label><input class="form-input" name="name" placeholder="Nguyễn Văn A" required /></div>
          <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email" placeholder="email@example.com" required /></div>
          <div class="form-group"><label class="form-label">Mật khẩu</label><input class="form-input" name="password" type="password" placeholder="Tối thiểu 6 ký tự" required /></div>
          <button type="submit" class="btn btn-primary w-full btn-lg">Tạo tài khoản</button>
          <p class="text-center mt-2 text-muted" style="font-size:.85rem">Đã có tài khoản? <a href="#/login" class="link">Đăng nhập</a></p>
        </form>
      </div>
    </div>`;

  document.getElementById('reg-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await Auth.registerCustomer({ name: fd.get('name'), email: fd.get('email'), password: fd.get('password') });
      toast('Đăng ký thành công! Hãy đăng nhập.', 'success');
      navigate('/login');
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── PROFILE ────────────────────────────────────
async function renderProfile() {
  if (!state.user) { navigate('/login'); return; }
  app.innerHTML = loading();
  const profile = await Customer.getProfile(state.user.user_id).catch(() => null);

  app.innerHTML = `
    <h1 class="section-title mb-4">👤 <span>Hồ Sơ</span></h1>
    <div class="profile-layout">
      <div class="profile-sidebar">
        <div class="avatar-lg">👤</div>
        <div class="fw-bold">${state.user.name}</div>
        <div class="tag mt-1">${state.user.user_type === 'staff' ? 'Nhân viên' : 'Khách hàng'}</div>
        <hr class="divider">
        <a href="#/orders" class="btn btn-ghost w-full mb-1">📦 Đơn hàng của tôi</a>
        <a href="#/wishlist" class="btn btn-ghost w-full">❤️ Danh sách yêu thích</a>
      </div>
      <div>
        <div class="card" style="padding:1.5rem;margin-bottom:1.5rem">
          <h3 class="fw-bold mb-3">Thông tin cá nhân</h3>
          <form id="profile-form">
            <div class="form-group"><label class="form-label">Số điện thoại</label><input class="form-input" name="phone" value="${profile?.phone || ''}" placeholder="0912 345 678" /></div>
            <div class="form-group"><label class="form-label">Giới thiệu bản thân</label><textarea class="form-input" name="bio" placeholder="Mô tả ngắn về bạn...">${profile?.bio || ''}</textarea></div>
            <button type="submit" class="btn btn-primary">Lưu thay đổi</button>
          </form>
        </div>
        <div class="card" style="padding:1.5rem">
          <h3 class="fw-bold mb-1">Điểm thành viên</h3>
          <div class="stat-value">${profile?.points || 0}</div>
          <div class="text-muted" style="font-size:.85rem">Hạng: ${profile?.membership_tier || 'Bronze'}</div>
        </div>
      </div>
    </div>`;

  document.getElementById('profile-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      if (profile) await Customer.updateProfile(state.user.user_id, { customer_id: state.user.user_id, phone: fd.get('phone'), bio: fd.get('bio') });
      else await Customer.createProfile({ customer_id: state.user.user_id, phone: fd.get('phone'), bio: fd.get('bio') });
      toast('Đã cập nhật hồ sơ!', 'success');
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── ORDERS ─────────────────────────────────────
async function renderOrders() {
  if (!state.user) { navigate('/login'); return; }
  app.innerHTML = loading();
  const orders = await Order.myOrders(state.user.user_id).catch(() => []);

  app.innerHTML = `
    <h1 class="section-title mb-4">📦 <span>Đơn Hàng</span></h1>
    ${orders.length ? orders.map(o => `
      <div class="card order-card mb-2">
        <div class="order-header">
          <span class="order-id">Đơn #${o.id}</span>
          <span class="order-status ${statusClass(o.status)}">${o.status}</span>
        </div>
        <div class="flex" style="justify-content:space-between">
          <div class="text-muted" style="font-size:.85rem">${new Date(o.date).toLocaleString('vi')}</div>
          <div class="fw-bold text-indigo">${fmt(o.total_price)}</div>
        </div>
        <div class="text-muted" style="font-size:.8rem;margin-top:.25rem">${o.total_quantity} sản phẩm${o.note ? ' · ' + o.note : ''}</div>
      </div>`).join('') : `
      <div class="empty">
        <div style="font-size:4rem">📦</div>
        <h3>Chưa có đơn hàng</h3>
        <a href="#/products" class="btn btn-primary">Mua sắm ngay</a>
      </div>`}`;
}

// ── WISHLIST ───────────────────────────────────
async function renderWishlist() {
  if (!state.user) { navigate('/login'); return; }
  app.innerHTML = loading();
  const wishlist = await Customer.wishlist(state.user.user_id).catch(() => null);
  const items = wishlist?.items || [];
  await Promise.all(items.map(async i => {
      if(!i.product_title) {
          const pid = i.product_id;
          const b = await Product.get(pid).catch(()=>null);
          i.product_title = b?.title || `Sản phẩm #${pid}`;
          i.author_name = b?.author_name || b?.category_name || '';
      }
  }));

  app.innerHTML = `
    <h1 class="section-title mb-4">❤️ <span>Yêu Thích</span></h1>
    ${items.length ? `
    <div class="grid-4">
      ${items.map(i => `
        <div class="card" style="padding:1rem">
          <div style="font-size:3rem;text-align:center;margin-bottom:.75rem">📖</div>
          <div class="fw-bold text-center mb-1" style="font-size:0.9rem">${i.product_title}</div><div class="text-muted text-center mb-2" style="font-size:0.75rem">${i.author_name}</div>
          <div class="flex gap-1">
            <a href="#/product/${i.product_id}" class="btn btn-outline btn-sm w-full">Xem</a>
            <button class="btn btn-danger btn-sm rm-wish" data-id="${i.product_id}">✕</button>
          </div>
        </div>`).join('')}
    </div>` : `<div class="empty"><div style="font-size:4rem">❤️</div><h3>Chưa có sản phẩm yêu thích</h3><a href="#/products" class="btn btn-primary mt-2">Khám phá sản phẩm</a></div>`}`;

  document.querySelectorAll('.rm-wish').forEach(b => b.addEventListener('click', async () => {
    await Customer.toggleWish(state.user.user_id, b.dataset.id);
    toast('Đã xóa khỏi Wishlist', 'info'); renderWishlist();
  }));
}

// ── STAFF DASHBOARD ────────────────────────────
async function renderStaffDashboard() {
  if (!state.user || state.user.user_type !== 'staff') { navigate('/login'); return; }
  app.innerHTML = loading();

  const pageSize = 10;
  let currentPage = 1;
  let products = [];
  let hasNextPage = false;

  const fetchProductsPage = async (page = 1) => {
    const skip = (page - 1) * pageSize;
    const result = await Product.list('', '', '', skip, pageSize + 1).catch(() => []);
    hasNextPage = result.length > pageSize;
    products = hasNextPage ? result.slice(0, pageSize) : result;
    currentPage = page;
    renderProductTable();
  };

  const renderProductTable = () => {
    const productSection = document.getElementById('product-manager-section');
    if (!productSection) return;
    productSection.innerHTML = `
      <div class="section-header">
        <h2 class="section-title" style="font-size:1.1rem">📦 Quản lý sản phẩm</h2>
        <button class="btn btn-primary btn-sm" id="add-product-btn">+ Thêm sản phẩm</button>
      </div>
      <div class="card">
        <div class="table-wrap table-scroll">
          <table>
            <thead><tr><th>Tên sản phẩm</th><th>Giá</th><th>Kho</th></tr></thead>
            <tbody>
              ${products.map(b => `
                <tr>
                  <td>${b.title}</td>
                  <td class="text-indigo">${fmt(b.price)}</td>
                  <td>${b.stock_quantity}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
        <div class="table-pagination">
          <button class="btn btn-secondary btn-sm" id="prev-products-btn" ${currentPage === 1 ? 'disabled' : ''}>‹ Trước</button>
          <span>Trang ${currentPage}${hasNextPage ? '' : ''}</span>
          <button class="btn btn-secondary btn-sm" id="next-products-btn" ${hasNextPage ? '' : 'disabled'}>Tiếp ›</button>
        </div>
      </div>`;

    document.getElementById('add-product-btn').onclick = () => showAddProductModal();
    document.getElementById('prev-products-btn').onclick = () => fetchProductsPage(currentPage - 1);
    document.getElementById('next-products-btn').onclick = () => fetchProductsPage(currentPage + 1);
  };

  const [statsRes, ordersRes, totalProductsRes] = await Promise.allSettled([
    Order.stats(), Order.allOrders(0), Product.list('', '', '', 0, 1000)
  ]);
  const stats = statsRes.value || [];
  const orders = ordersRes.value || [];
  const totalProducts = totalProductsRes.value || [];

  const totalRev = stats.reduce((s, r) => s + (r.total_revenue || 0), 0);
  const totalOrd = stats.reduce((s, r) => s + (r.count || 0), 0);

  app.innerHTML = `
    <h1 class="section-title mb-4">📊 <span>Staff Dashboard</span></h1>
    <div class="stats-grid mb-4">
      <div class="stat-card"><div class="stat-value">${totalOrd}</div><div class="stat-label">Tổng đơn hàng</div></div>
      <div class="stat-card"><div class="stat-value">${fmt(totalRev)}</div><div class="stat-label">Doanh thu</div></div>
      <div class="stat-card"><div class="stat-value">${totalProducts.length}</div><div class="stat-label">Sản phẩm hiện có</div></div>
      <div class="stat-card"><div class="stat-value">${stats.find(s => s.status === 'PENDING')?.count || 0}</div><div class="stat-label">Đơn chờ xử lý</div></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem">
      <div>
        <div class="section-header">
          <h2 class="section-title" style="font-size:1.1rem">📦 Đơn hàng gần đây</h2>
        </div>
        <div class="card">
          <div class="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>Khách</th><th>Tổng</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
              <tbody>
                ${orders.slice(0, 10).map(o => `
                  <tr>
                    <td>#${o.id}</td>
                    <td>#${o.customer_id}</td>
                    <td class="text-indigo fw-bold">${fmt(o.total_price)}</td>
                    <td><span class="order-status ${statusClass(o.status)}">${o.status}</span></td>
                    <td>
                      <select class="form-input" style="padding:.2rem .4rem;font-size:.75rem;width:auto" onchange="updateOrderStatus(${o.id},this.value)">
                        <option>PENDING</option><option>PROCESSING</option>
                        <option>SHIPPED</option><option>DELIVERED</option><option>CANCELLED</option>
                      </select>
                    </td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div id="product-manager-section"></div>
    </div>`;

  await fetchProductsPage(1);
}

async function updateOrderStatus(orderId, status) {
  try { await Order.updateStatus(orderId, status); toast(`Đã cập nhật đơn #${orderId} → ${status}`, 'success'); }
  catch (e) { toast(e.message, 'error'); }
}

function showAddProductModal() {
  openModal(`
    <h3 class="fw-bold mb-3">Thêm sản phẩm mới</h3>
    <form id="add-product-form">
      <div class="form-group"><label class="form-label">Tên sản phẩm *</label><input class="form-input" name="title" required /></div>
      <div class="form-group"><label class="form-label">Giá (đồng) *</label><input class="form-input" name="price" type="number" required /></div>
      <div class="form-group"><label class="form-label">Số lượng tồn kho</label><input class="form-input" name="stock" type="number" value="50" /></div>
      <div class="form-group"><label class="form-label">SKU</label><input class="form-input" name="sku" type="text" placeholder="VD: STA-001" /></div>
      <div class="form-group"><label class="form-label">Mô tả</label><textarea class="form-input" name="description" rows="3"></textarea></div>
      <button type="submit" class="btn btn-primary w-full">Tạo sản phẩm</button>
    </form>`);

  document.getElementById('add-product-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await Product.create({
        name: fd.get('title'), sku: fd.get('sku') || ('SKU-' + Date.now()), price: parseFloat(fd.get('price')),
        stock_quantity: parseInt(fd.get('stock')) || 50,
        description: fd.get('description'), attributes: {}
      });
      toast('Đã thêm sản phẩm!', 'success'); closeModal(); renderStaffDashboard();
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── MARKETING ──────────────────────────────────
async function renderMarketing() {
  app.innerHTML = loading();
  const [couponsRes, flashRes, promosRes] = await Promise.allSettled([
    Marketing.coupons(), Marketing.flashSales(), Marketing.promotions()
  ]);
  const coupons = couponsRes.value || [];
  const flash = flashRes.value || [];
  const promos = promosRes.value || [];

  app.innerHTML = `
    <h1 class="section-title mb-4">🎁 <span>Khuyến Mãi</span></h1>
    ${state.user?.user_type === 'staff' ? `<button class="btn btn-primary btn-sm mb-4" id="new-coupon-btn">+ Tạo coupon mới</button>` : ''}

    <div class="section-header"><h2 class="section-title" style="font-size:1.1rem">🎟 Mã Giảm Giá</h2></div>
    <div class="grid-2 mb-4">
      ${coupons.length ? coupons.map(c => `
        <div class="coupon-card">
          <div>
            <div class="coupon-code">${c.code}</div>
            <div class="text-muted" style="font-size:.8rem">
              ${c.discount_percent ? `-${c.discount_percent}%` : `-${fmt(c.discount_amount)}`}
              · Đơn tối thiểu ${fmt(c.min_order_value)}
            </div>
          </div>
        </div>`).join('') : '<p class="text-muted">Chưa có mã giảm giá.</p>'}
    </div>

    <div class="section-header"><h2 class="section-title" style="font-size:1.1rem">⚡ Flash Sale</h2></div>
    <div class="grid-3 mb-4">
      ${flash.map(s => `
        <div class="flash-sale-card">
          <div class="tag tag-purple mb-2">-${s.discount_percent}%</div>
          <h3 class="fw-bold">${s.name}</h3>
          <div class="text-muted" style="font-size:.8rem;margin-top:.5rem">Số lượng: ${s.max_quantity || '∞'} · Đã bán: ${s.sold_quantity}</div>
          <div class="text-muted" style="font-size:.75rem">Đến: ${new Date(s.end_at).toLocaleString('vi')}</div>
        </div>`).join('') || '<p class="text-muted">Không có flash sale nào.</p>'}
    </div>

    <div class="section-header"><h2 class="section-title" style="font-size:1.1rem">📢 Chương Trình Khuyến Mãi</h2></div>
    <div class="grid-3">
      ${promos.map(p => `
        <div class="card" style="padding:1.25rem">
          ${p.discount_percent ? `<div class="tag mb-2">-${p.discount_percent}%</div>` : ''}
          <h3 class="fw-bold mb-1">${p.name}</h3>
          <p class="text-muted" style="font-size:.85rem">${p.description || ''}</p>
        </div>`).join('') || '<p class="text-muted">Không có chương trình khuyến mãi.</p>'}
    </div>`;

  document.getElementById('new-coupon-btn')?.addEventListener('click', showCreateCouponModal);
}

function showCreateCouponModal() {
  openModal(`
    <h3 class="fw-bold mb-3">Tạo coupon mới</h3>
    <form id="coupon-form">
      <div class="form-group"><label class="form-label">Mã coupon *</label><input class="form-input" name="code" placeholder="SAVE20" required /></div>
      <div class="form-group"><label class="form-label">Giảm % (để trống nếu giảm tiền)</label><input class="form-input" name="discount_percent" type="number" /></div>
      <div class="form-group"><label class="form-label">Giảm tiền (đồng)</label><input class="form-input" name="discount_amount" type="number" /></div>
      <div class="form-group"><label class="form-label">Đơn tối thiểu</label><input class="form-input" name="min_order_value" type="number" value="0" /></div>
      <div class="form-group"><label class="form-label">Số lần dùng tối đa</label><input class="form-input" name="max_uses" type="number" /></div>
      <button type="submit" class="btn btn-primary w-full">Tạo coupon</button>
    </form>`);

  document.getElementById('coupon-form').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await Marketing.createCoupon({
        code: fd.get('code').toUpperCase(),
        discount_percent: fd.get('discount_percent') ? parseFloat(fd.get('discount_percent')) : null,
        discount_amount: fd.get('discount_amount') ? parseFloat(fd.get('discount_amount')) : null,
        min_order_value: parseFloat(fd.get('min_order_value')) || 0,
        max_uses: fd.get('max_uses') ? parseInt(fd.get('max_uses')) : null,
      });
      toast('Đã tạo coupon!', 'success'); closeModal(); renderMarketing();
    } catch (e) { toast(e.message, 'error'); }
  };
}

// ── NOTIFICATIONS ──────────────────────────────
async function renderNotifications() {
  if (!state.user) { navigate('/login'); return; }
  app.innerHTML = loading();
  const notifs = await Notification.mine(state.user.user_id).catch(() => []);

  app.innerHTML = `
    <h1 class="section-title mb-4">🔔 <span>Thông Báo</span></h1>
    ${notifs.length ? notifs.map(n => `
      <div class="card" style="padding:1rem;margin-bottom:.75rem;opacity:${n.is_read ? .6 : 1};cursor:pointer" onclick="markRead(${n.id},this)">
        <div class="flex" style="justify-content:space-between;margin-bottom:.3rem">
          <span class="fw-bold">${n.title}</span>
          <span class="tag tag-${n.notification_type === 'ORDER' ? 'indigo' : n.notification_type === 'PROMOTION' ? 'purple' : 'cyan'}" style="font-size:.7rem">${n.notification_type}</span>
        </div>
        <p style="font-size:.88rem;">${n.message}</p>
        <div class="text-muted" style="font-size:.75rem;margin-top:.3rem">${new Date(n.created_at).toLocaleString('vi')}</div>
      </div>`).join('') : `<div class="empty"><div style="font-size:3rem">🔔</div><h3>Chưa có thông báo</h3></div>`}`;
}

async function markRead(id, el) {
  try { await Notification.read(id); el.style.opacity = '.6'; } catch { }
}

// ── User menu toggle ────────────────────────────
document.getElementById('user-menu-btn')?.addEventListener('click', e => {
  e.stopPropagation();
  document.getElementById('user-dropdown').classList.toggle('open');
});
document.addEventListener('click', () => document.getElementById('user-dropdown')?.classList.remove('open'));
document.getElementById('logout-btn')?.addEventListener('click', logout);

// ── Fixed light theme ─────────────────────────
localStorage.removeItem('app-theme');
document.documentElement.setAttribute('data-theme', 'light');
