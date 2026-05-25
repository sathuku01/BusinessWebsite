# TODO

- [ ] Inspect and update payment form view rendering logic
  - [ ] Replace `add_payment` in `ecommerce/views.py` to only supply orders with outstanding balance > 0
  - [ ] Replace `update_payment` in `ecommerce/views.py` similarly
  - [ ] Ensure required imports (`timezone`, `get_object_or_404`) exist
- [ ] Update `ecommerce/templates/ecommerce/payment_form.html`
  - [ ] Replace order dropdown HTML to show only unpaid orders (using `orders` passed from views)
  - [ ] Replace balance box HTML (`#balanceBox`)
  - [ ] Replace bottom `<script>` with new logic that pre-fills amount and updates balance box immediately
- [ ] Validate
  - [ ] Run `python manage.py check`
  - [ ] Open payment form URL and verify dropdown + balance box behavior

