const API = {
  auth: 'http://localhost:8001',
  product: 'http://localhost:8002',
  order: 'http://localhost:8003',
  customer: 'http://localhost:8004',
  staff: 'http://localhost:8005',
  marketing: 'http://localhost:8006',
  inventory: 'http://localhost:8007',
  content: 'http://localhost:8008',
  interaction: 'http://localhost:8009',
  analytics: 'http://localhost:8010',
  notification: 'http://localhost:8011',
  behavior: 'http://localhost:8013',
};

async function req(url, opts = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(url, { ...opts, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.status === 204 ? null : res.json();
}
const get = (url) => req(url);
const post = (url, body) => req(url, { method: 'POST', body: JSON.stringify(body) });
const put = (url, body) => req(url, { method: 'PUT', body: JSON.stringify(body) });
const del = (url) => req(url, { method: 'DELETE' });
const patch = (url, body) => req(url, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined });

const Auth = {
  registerCustomer: b => post(`${API.auth}/register/customer`, b),
  registerStaff: b => post(`${API.auth}/register/staff`, b),
  loginCustomer: b => post(`${API.auth}/login/customer`, b),
  loginStaff: b => post(`${API.auth}/login/staff`, b),
  me: token => get(`${API.auth}/me?token=${token}`),
  verifyToken: token => get(`${API.auth}/verify-token?token=${token}`),
  customers: () => get(`${API.auth}/customers`),
};

const Product = {
  list: (search = '', category_id = '', product_type_id = '', skip = 0, limit = 20) => {
    const p = new URLSearchParams();
    if (search) p.set('q', search);
    if (category_id) p.set('category_id', category_id);
    if (product_type_id) p.set('product_type_id', product_type_id);
    p.set('skip', skip); p.set('limit', limit);
    return get(`${API.product}/products?${p.toString()}`);
  },
  get: id => get(`${API.product}/products/${id}`),
  create: b => post(`${API.product}/products`, b),
  update: (id, b) => put(`${API.product}/products/${id}`, b),
  delete: id => del(`${API.product}/products/${id}`),
  updateStock: (id, q) => patch(`${API.product}/products/${id}/stock?quantity=${q}`),
  categories: () => get(`${API.product}/categories`),
  productTypes: () => get(`${API.product}/product-types`),
  brands: () => get(`${API.product}/brands`),
  createCategory: b => post(`${API.product}/categories`, b),
  createProductType: b => post(`${API.product}/product-types`, b),
  createBrand: b => post(`${API.product}/brands`, b),
  getRatings: id => get(`${API.product}/products/${id}/ratings`),
  rate: b => post(`${API.product}/ratings`, b),
  getReviews: id => get(`${API.product}/products/${id}/reviews`),
  review: b => post(`${API.product}/reviews`, b),
};

const Order = {
  cart: cid => get(`${API.order}/cart/${cid}`),
  cartSummary: cid => get(`${API.order}/cart/${cid}/summary`),
  addToCart: (cid, b) => post(`${API.order}/cart/${cid}/add`, { ...b, product_id: b.product_id ?? b.book_id }),
  updateQty: (cid, iid, qty) => patch(`${API.order}/cart/${cid}/item/${iid}/quantity?quantity=${qty}`),
  removeItem: (cid, iid) => del(`${API.order}/cart/${cid}/item/${iid}`),
  clearCart: cid => del(`${API.order}/cart/${cid}/clear`),
  checkout: b => post(`${API.order}/checkout`, b),
  myOrders: cid => get(`${API.order}/orders/customer/${cid}`),
  allOrders: (skip = 0, status = '') => get(`${API.order}/orders?skip=${skip}${status ? '&status=' + status : ''}`),
  getOrder: id => get(`${API.order}/orders/${id}`),
  orderItems: id => get(`${API.order}/orders/${id}/items`),
  updateStatus: (id, st) => patch(`${API.order}/orders/${id}/status?status=${st}`),
  stats: () => get(`${API.order}/orders/stats/summary`),
};

const Customer = {
  getProfile: cid => get(`${API.customer}/profile/${cid}`),
  createProfile: b => post(`${API.customer}/profile`, b),
  updateProfile: (cid, b) => put(`${API.customer}/profile/${cid}`, b),
  wishlist: cid => get(`${API.customer}/wishlist/${cid}`),
  toggleWish: (cid, pid) => post(`${API.customer}/wishlist/${cid}/toggle/${pid}`),
  addresses: cid => get(`${API.customer}/addresses/${cid}`),
  addAddress: b => post(`${API.customer}/addresses`, b),
  subscribe: b => post(`${API.customer}/newsletter/subscribe`, b),
};

const Marketing = {
  coupons: () => get(`${API.marketing}/coupons`),
  createCoupon: b => post(`${API.marketing}/coupons`, b),
  validateCoupon: (code, tot) => get(`${API.marketing}/coupons/validate/${code}?order_total=${tot}`),
  promotions: () => get(`${API.marketing}/promotions`),
  createPromo: b => post(`${API.marketing}/promotions`, b),
  flashSales: () => get(`${API.marketing}/flash-sales`),
  createFlash: b => post(`${API.marketing}/flash-sales`, { ...b, product_id: b.product_id ?? b.book_id }),
  tiers: () => get(`${API.marketing}/tiers`),
  seedTiers: () => post(`${API.marketing}/tiers/seed`),
  referral: cid => post(`${API.marketing}/referrals/${cid}`),
};

const Analytics = {
  sales: () => get(`${API.analytics}/sales`),
  logSearch: b => post(`${API.analytics}/search-history`, b),
  recentViewed: cid => get(`${API.analytics}/recently-viewed/${cid}`),
  logView: b => post(`${API.analytics}/recently-viewed`, { ...b, product_id: b.product_id ?? b.book_id }),
};

const Content = {
  banners: () => get(`${API.content}/banners`),
  collections: () => get(`${API.content}/collections`),
  blog: () => get(`${API.content}/blog`),
};

const Notification = {
  mine: cid => get(`${API.notification}/notifications/${cid}`),
  create: b => post(`${API.notification}/notifications`, b),
  read: id => patch(`${API.notification}/notifications/${id}/read`),
};

const Interaction = {
  loyalty: cid => get(`${API.interaction}/loyalty-points/${cid}`),
  giftCard: code => get(`${API.interaction}/gift-cards/${code}`),
  buyGiftCard: b => post(`${API.interaction}/gift-cards`, b),
};

const Inventory = {
  suppliers: () => get(`${API.inventory}/suppliers`),
  warehouses: () => get(`${API.inventory}/warehouses`),
  alerts: () => get(`${API.inventory}/alerts`),
  logAlert: b => post(`${API.inventory}/alerts`, b),
};

const Behavior = {
  track: b => post(`${API.behavior}/events`, { ...b, product_id: b.product_id ?? b.book_id }),
  profile: cid => get(`${API.behavior}/profiles/${cid}`),
  features: cid => get(`${API.behavior}/features/${cid}`),
};

const AI = {
  recommendations: (limit = 6) => get(`http://localhost:8012/recommendations?limit=${limit}`),
  ask: question => post('http://localhost:8012/chat/ask', { question }),
};
