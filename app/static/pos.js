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
  let searchTimeout = null;
  let allItems = []; // Cache all items for search

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
    saveCart(); 
    render();
    
    // Show feedback
    if (window.showToast) {
      window.showToast(`Added ${name}`, 'success', 1000);
    }
  }
  
  function setQty(id, qty) {
    id = Number(id); qty = Math.max(0, qty || 0);
    if (!cart[id]) return;
    if (qty === 0) delete cart[id]; else cart[id].qty = qty;
    saveCart(); render();
  }
  
  function removeItem(id) {
    id = Number(id);
    if (cart[id]) { 
      const itemName = cart[id].name;
      delete cart[id]; 
      saveCart(); 
      render();
      
      // Show feedback
      if (window.showToast) {
        window.showToast(`Removed ${itemName}`, 'info', 1000);
      }
    }
  }
  
  function clearCart() { 
    cart = {}; 
    saveCart(); 
    render();
    
    // Show feedback
    if (window.showToast) {
      window.showToast('Cart cleared', 'info', 1000);
    }
  }

  function toPaisa(rupeesStr) {
    const n = parseFloat(rupeesStr || '0');
    if (isNaN(n)) return 0;
    return Math.round(n * 100);
  }

  function checkout() {
    const lines = Object.values(cart).map(l => ({item_id: l.id, qty: l.qty}));
    if (lines.length === 0) { 
      if (window.showToast) {
        window.showToast('Cart is empty', 'error', 2000);
      } else {
        alert('Cart is empty.');
      }
      return; 
    }
    
    // Validate cash payment
    if (paySel.value === 'cash') {
      const cashReceived = parseFloat(cashIn.value || '0');
      if (cashReceived < lastTotalCents / 100) {
        if (window.showToast) {
          window.showToast('Insufficient cash received', 'error', 3000);
        } else {
          alert('Insufficient cash received');
        }
        return;
      }
    }
    
    cartJsonEl.value = JSON.stringify(lines);
    formPay.value = paySel.value;
    if (paySel.value === 'cash' && (!cashIn.value || cashWasAuto)) {
      cashIn.value = (lastTotalCents / 100).toFixed(2);
    }
    formCash.value = String(toPaisa(cashIn.value));
    formNote.value = noteEl.value || '';
    
    // Show loading state
    const checkoutBtn = document.getElementById('checkout');
    if (checkoutBtn) {
      checkoutBtn.disabled = true;
      checkoutBtn.textContent = 'Processing...';
    }
    
    // Order number will be stored by the print template after order creation
    
    form.submit();
    clearCart();
  }

  // Items and Tabs
  const tabEls = Array.from(document.querySelectorAll('.tab'));
  const grids = Array.from(document.querySelectorAll('.items-grid'));

  function showCat(cat) {
    tabEls.forEach(b => {
      const isActive = b.dataset.cat === cat;
      b.classList.toggle('active', isActive);
    });
    grids.forEach(g => {
      const shouldShow = g.dataset.cat === cat;
      g.hidden = !shouldShow;
    });
    localStorage.setItem('pos_last_cat', cat);
    filterCards(); // apply search filter for the visible cat
  }

  tabEls.forEach(btn => btn.addEventListener('click', () => showCat(btn.dataset.cat)));

  // Default category: remember last or pick the first
  const lastCat = localStorage.getItem('pos_last_cat');
  const firstTab = tabEls[0];
  const startCat = (lastCat && tabEls.find(t => t.dataset.cat === lastCat)) ? lastCat : (firstTab ? firstTab.dataset.cat : null);
  
  if (startCat) {
    showCat(startCat);
  }

  // Cache all items for search
  function cacheItems() {
    allItems = Array.from(document.querySelectorAll('.item-btn')).map(btn => ({
      id: btn.dataset.id,
      name: btn.dataset.name,
      price: Number(btn.dataset.price),
      category: btn.dataset.cat,
      element: btn
    }));
  }

  // Enhanced search with debouncing
  function enhancedSearch() {
    const query = (searchIn.value || '').trim().toLowerCase();
    
    if (query.length < 2) {
      // Show all items in current category
      filterCards();
      return;
    }
    
    // Search across all items
    allItems.forEach(item => {
      const matches = item.name.toLowerCase().includes(query) || 
                     item.category.toLowerCase().includes(query);
      item.element.style.display = matches ? '' : 'none';
    });
    
    // Show all categories that have matching items
    const matchingCategories = new Set();
    allItems.forEach(item => {
      if (item.name.toLowerCase().includes(query)) {
        matchingCategories.add(item.category);
      }
    });
    
    // Update tab visibility
    tabEls.forEach(tab => {
      const isVisible = matchingCategories.has(tab.dataset.cat);
      tab.style.display = isVisible ? '' : 'none';
    });
    
    // Show first matching category
    const firstMatchingTab = tabEls.find(tab => matchingCategories.has(tab.dataset.cat));
    if (firstMatchingTab && !firstMatchingTab.classList.contains('active')) {
      showCat(firstMatchingTab.dataset.cat);
    }
  }

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

  // Enhanced search filter with debouncing
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
  
  searchIn.addEventListener('input', () => {
    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Debounce search
    searchTimeout = setTimeout(() => {
      if (searchIn.value.trim().length >= 2) {
        enhancedSearch();
      } else {
        filterCards();
      }
    }, 300);
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
      return;
    }
    
    // Ctrl/Cmd + Enter to checkout
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      checkout();
    }
    
    // Escape to clear cart
    if (e.key === 'Escape') {
      e.preventDefault();
      clearCart();
    }
    
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchIn.focus();
    }
    
    // Number keys to quick add items (1-9)
    if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.metaKey) {
      const visibleItems = Array.from(document.querySelectorAll('.items-grid:not([hidden]) .item-btn'));
      const index = parseInt(e.key) - 1;
      if (visibleItems[index]) {
        e.preventDefault();
        const item = visibleItems[index];
        addItem(item.dataset.id, item.dataset.name, Number(item.dataset.price));
      }
    }
  });

  // Buttons
  document.getElementById('clear').addEventListener('click', clearCart);
  document.getElementById('checkout').addEventListener('click', checkout);
  
  // Reprint last order functionality
  document.getElementById('reprintLast')?.addEventListener('click', () => {
    const lastOrderNumber = localStorage.getItem('last_order_number');
    if (lastOrderNumber) {
      // First try to get the order by number to get the ID
      fetch(`/api/orders/${lastOrderNumber}`)
        .then(response => response.json())
        .then(data => {
          const orderId = data.order.id;
          window.open(`/print/customer/${orderId}`, '_blank');
          setTimeout(() => {
            window.open(`/print/kitchen/${orderId}`, '_blank');
          }, 1000);
        })
        .catch(() => {
          if (window.showToast) {
            window.showToast('Could not find order to reprint', 'error', 2000);
          } else {
            alert('Could not find order to reprint');
          }
        });
    } else {
      if (window.showToast) {
        window.showToast('No recent order to reprint', 'error', 2000);
      } else {
        alert('No recent order to reprint');
      }
    }
  });

  // Initialize
  loadCart();
  render();
  cacheItems();
  
  // Show welcome message
  if (window.showToast && Object.keys(cart).length === 0) {
    setTimeout(() => {
      window.showToast('Welcome! Use Ctrl+K to search, Ctrl+Enter to checkout', 'info', 4000);
    }, 1000);
  }
})();