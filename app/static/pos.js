(function() {
  const cartEl = document.getElementById('cart');
  const subtotalEl = document.getElementById('subtotal');
  const taxEl = document.getElementById('tax');
  const totalEl = document.getElementById('total');
  const changeEl = document.getElementById('change');
  const changeRow = document.getElementById('changeRow');
  const noteEl = document.getElementById('note');
  const paySel = document.getElementById('payment_method');
  const cashWrap = document.getElementById('cashWrap');
  const cashIn = document.getElementById('cash_received');
  const searchIn = document.getElementById('search');
  const form = document.getElementById('checkout_form');
  const cartJsonEl = document.getElementById('cart_json');
  const formPay = document.getElementById('form_payment_method');
  const formCash = document.getElementById('form_cash_received');
  const formNote = document.getElementById('form_note');

  let cart = {}; // id -> {id, name, price_cents, qty}
  let lastTotalCents = 0;
  let cashWasAuto = false; // tracks whether the current cash value was auto-filled

  function money(cents) { return 'Rs ' + (cents/100).toFixed(2); }

  function loadCart() {
    try {
      const raw = localStorage.getItem('crispino_cart');
      if (raw) cart = JSON.parse(raw) || {};
    } catch {}
  }
  function saveCart() { localStorage.setItem('crispino_cart', JSON.stringify(cart)); }

  function maybeDefaultCash(totalCents) {
    if (paySel.value !== 'cash') return;
    if (!cashIn.value || cashWasAuto) {
      cashIn.value = (totalCents / 100).toFixed(2);
      cashWasAuto = true;
    }
  }

  function updateChange() {
    if (paySel.value !== 'cash') { changeRow.hidden = true; return; }
    const n = parseFloat(cashIn.value || '0'); const paid = isNaN(n) ? 0 : Math.round(n * 100);
    const change = Math.max(0, paid - lastTotalCents);
    changeEl.textContent = money(change);
    changeRow.hidden = false;
  }

  function render() {
    cartEl.innerHTML = '';
    let subtotal = 0;
    Object.values(cart).forEach(line => {
      const lineTotal = line.price_cents * line.qty;
      subtotal += lineTotal;

      const row = document.createElement('div');
      row.className = 'cart-line';

      const name = document.createElement('div');
      name.textContent = line.name;

      const qtyCtl = document.createElement('div');
      qtyCtl.className = 'qty-control';
      const minus = document.createElement('button'); minus.textContent = '−';
      const input = document.createElement('input'); input.type='number'; input.value = line.qty; input.min = '0';
      const plus = document.createElement('button'); plus.textContent = '+';

      minus.addEventListener('click', () => { setQty(line.id, line.qty - 1); });
      plus.addEventListener('click', () => { setQty(line.id, line.qty + 1); });
      input.addEventListener('change', () => { setQty(line.id, parseInt(input.value || '0', 10)); });

      qtyCtl.appendChild(minus); qtyCtl.appendChild(input); qtyCtl.appendChild(plus);

      const price = document.createElement('div');
      price.className = 'price';
      price.textContent = money(lineTotal);

      const remove = document.createElement('button');
      remove.className = 'remove';
      remove.textContent = '×';
      remove.title = 'Remove';
      remove.addEventListener('click', () => { removeItem(line.id); });

      row.appendChild(name); row.appendChild(qtyCtl); row.appendChild(price); row.appendChild(remove);
      cartEl.appendChild(row);
    });

    const tax = Math.round(subtotal * (TAX_RATE / 100));
    const total = subtotal + tax;

    subtotalEl.textContent = money(subtotal);
    taxEl.textContent = money(tax);
    totalEl.textContent = money(total);

    lastTotalCents = total;
    maybeDefaultCash(total);
    updateChange();
  }

  function addItem(id, name, price_cents) {
    id = Number(id);
    if (!cart[id]) { cart[id] = {id, name, price_cents, qty: 0}; }
    cart[id].qty += 1;
    saveCart(); render();
  }
  function setQty(id, qty) {
    id = Number(id); qty = Math.max(0, qty || 0);
    if (!cart[id]) return;
    if (qty === 0) delete cart[id]; else cart[id].qty = qty;
    saveCart(); render();
  }
  function removeItem(id) {
    id = Number(id);
    if (cart[id]) { delete cart[id]; saveCart(); render(); }
  }
  function clearCart() { cart = {}; saveCart(); render(); }

  function toPaisa(rupeesStr) {
    const n = parseFloat(rupeesStr || '0');
    if (isNaN(n)) return 0;
    return Math.round(n * 100);
  }

  function checkout() {
    const lines = Object.values(cart).map(l => ({item_id: l.id, qty: l.qty}));
    if (lines.length === 0) { alert('Cart is empty.'); return; }
    cartJsonEl.value = JSON.stringify(lines);
    formPay.value = paySel.value;
    if (paySel.value === 'cash' && (!cashIn.value || cashWasAuto)) {
      cashIn.value = (lastTotalCents / 100).toFixed(2);
    }
    formCash.value = String(toPaisa(cashIn.value));
    formNote.value = noteEl.value || '';
    form.submit();
    clearCart();
  }

  // Items and Tabs
  const tabEls = Array.from(document.querySelectorAll('.tab'));
  const grids = Array.from(document.querySelectorAll('.items-grid'));

  function showCat(cat) {
    tabEls.forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
    grids.forEach(g => g.hidden = g.dataset.cat !== cat);
    localStorage.setItem('pos_last_cat', cat);
    filterCards(); // apply search filter for the visible cat
  }

  tabEls.forEach(btn => btn.addEventListener('click', () => showCat(btn.dataset.cat)));

  // Default category: remember last or pick the first
  const lastCat = localStorage.getItem('pos_last_cat');
  const firstTab = tabEls[0];
  const startCat = (lastCat && tabEls.find(t => t.dataset.cat === lastCat)) ? lastCat : (firstTab ? firstTab.dataset.cat : null);
  if (startCat) showCat(startCat);

  // Wire item buttons
  document.querySelectorAll('.item-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      addItem(btn.dataset.id, btn.dataset.name, Number(btn.dataset.price));
    });
  });

  // Payment behavior
  function updatePaymentUI() {
    const isCash = paySel.value === 'cash';
    cashWrap.style.display = isCash ? '' : 'none';
    maybeDefaultCash(lastTotalCents);
    updateChange();
  }
  paySel.addEventListener('change', updatePaymentUI);
  updatePaymentUI();

  cashIn.addEventListener('input', () => { cashWasAuto = false; updateChange(); });

  // Search filter (current category)
  function filterCards() {
    const q = (searchIn.value || '').trim().toLowerCase();
    const active = document.querySelector('.items-grid:not([hidden])');
    if (!active) return;
    const cards = active.querySelectorAll('.card');
    cards.forEach(c => {
      const name = c.querySelector('.card-title')?.textContent?.toLowerCase() || '';
      const show = !q || name.includes(q);
      c.style.display = show ? '' : 'none';
    });
  }
  searchIn.addEventListener('input', filterCards);

  // Buttons
  document.getElementById('clear').addEventListener('click', clearCart);
  document.getElementById('checkout').addEventListener('click', checkout);

  // Init
  loadCart();
  render();
})();