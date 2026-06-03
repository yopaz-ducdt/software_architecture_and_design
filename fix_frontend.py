import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Properly conditionally render register button
# The previous replace left a literal \` due to JSON escaping.
content = content.replace(
    r"${!state.user ? \`<a href=\"#/register\" class=\"btn btn-outline btn-lg\">Đăng ký miễn phí</a>\` : ''}",
    "${!state.user ? '<a href=\"#/register\" class=\"btn btn-outline btn-lg\">Đăng ký miễn phí</a>' : ''}"
)
content = content.replace(
    r"${!state.user ? `\<a href=\"#/register\" class=\"btn btn-outline btn-lg\"\>Đăng ký miễn phí\</a\>` : ''}",
    "${!state.user ? '<a href=\"#/register\" class=\"btn btn-outline btn-lg\">Đăng ký miễn phí</a>' : ''}"
)
# just in case it's actually exactly this:
content = re.sub(
    r"\$\{!state\.user \? [^\:]+ \: ''\}",
    "${!state.user ? '<a href=\"#/register\" class=\"btn btn-outline btn-lg\">Đăng ký miễn phí</a>' : ''}",
    content
)

# Fix 2: Object property names from backend (stock_quantity, cover_image_url, etc)
content = content.replace('b.stock < 10', '(b.stock_quantity || 0) < 10')
content = content.replace('b.stock < 1 ?', '(b.stock_quantity || 0) < 1 ?')
content = content.replace('Còn ${b.stock}', 'Còn ${b.stock_quantity || 0}')
content = content.replace('b.stock}', 'b.stock_quantity}')
content = content.replace('b.stock <', '(b.stock_quantity || 0) <')
content = content.replace('b.cover_image', 'b.cover_image_url')

# Fix 3: Fetch book titles for Cart
cart_fetch_logic = """  const items = cart?.items || [];
  // Fetch book details for cart items
  await Promise.all(items.map(async i => {
      if(!i.book_title) {
          const b = await Book.get(i.book_id).catch(()=>null);
          i.book_title = b?.title || `Sách #${i.book_id}`;
          i.author_name = b?.author_name || 'Khuyết danh';
      }
  }));"""

content = content.replace('  const items = cart?.items || [];', cart_fetch_logic)

# Update Cart UI to show author
content = content.replace(
    '<div class="cart-item-title">Sách #${i.book_id}</div>',
    '<div class="cart-item-title">${i.book_title}</div><div class="text-muted" style="font-size:0.8rem">${i.author_name}</div>'
)

# Fix 4: Fetch book titles for Wishlist
wishlist_fetch_logic = """  const items = wishlist?.items || [];
  await Promise.all(items.map(async i => {
      if(!i.book_title) {
          const b = await Book.get(i.book_id).catch(()=>null);
          i.book_title = b?.title || `Sách #${i.book_id}`;
          i.author_name = b?.author_name || '';
      }
  }));"""

content = content.replace('  const items = wishlist?.items || [];', wishlist_fetch_logic)

# Update Wishlist UI
content = content.replace(
    '<div class="fw-bold text-center mb-2">Sách #${i.book_id}</div>',
    '<div class="fw-bold text-center mb-1" style="font-size:0.9rem">${i.book_title}</div><div class="text-muted text-center mb-2" style="font-size:0.75rem">${i.author_name}</div>'
)

# Fix 5: Handle API returning objects for empty reviews/ratings
content = content.replace(
    'const reviews = reviewsRes.value || [];',
    'const reviews = Array.isArray(reviewsRes.value) ? reviewsRes.value : [];'
)
content = content.replace(
    'const ratings = ratingsRes.value || [];',
    'const ratings = Array.isArray(ratingsRes.value) ? ratingsRes.value : [];'
)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed app.js logic")
