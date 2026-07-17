# payment_templates.py

PAYPAL_CHECKOUT_HTML = """
<div class="paypal-checkout-container" style="max-width: 480px; margin: 0 auto; font-family: sans-serif; padding: 10px;">
    
    <!-- A. Seat Input -->
    <div style="margin-bottom: 15px;">
        <label for="seat-input" style="display: block; font-weight: bold; margin-bottom: 5px;">Number of Seats:</label>
        <input type="number" id="seat-input" value="40" min="1" max="100" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;" />
    </div>

    <!-- B. Order Summary -->
    <div id="order-summary-box" style="border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 6px; background-color: #f9f9f9;">
        <h3 style="margin-top: 0; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px;">Order Summary</h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>Selected Plan:</span>
            <strong>CPMS Classroom Basic</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>Seats Selected:</span>
            <span id="summary-seats">40</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>Price per Seat:</span>
            <span id="summary-unit-price">$5.00 / month</span>
        </div>
        <hr style="border: 0; border-top: 1px solid #ddd; margin: 12px 0;" />
        <div style="display: flex; justify-content: space-between; font-size: 1.1em; font-weight: bold;">
            <span>Estimated Total:</span>
            <span id="summary-total-price" style="color: #0070ba;">$200.00 / month</span>
        </div>
    </div>

    <!-- C. PayPal Button target -->
    <div id="paypal-button-container"></div>

</div>

<!-- D. Load PayPal SDK -->
<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&vault=true&intent=subscription"></script>

<!-- E. Dynamic logic and SDK initialization -->
<script>
  const seatInput = document.getElementById('seat-input');
  const summarySeats = document.getElementById('summary-seats');
  const summaryUnitPrice = document.getElementById('summary-unit-price');
  const summaryTotal = document.getElementById('summary-total-price');

  const TIER_1_LIMIT = 40;
  const TIER_1_RATE = 5.00; // $5/seat for 1-40
  const TIER_2_RATE = 4.00; // $4/seat for 41-100

  function updateSummary() {
    const seats = parseInt(seatInput.value) || 0;
    let rate = TIER_1_RATE;
    
    if (seats > TIER_1_LIMIT) {
      rate = TIER_2_RATE;
    }
    
    const total = seats * rate;
    
    summarySeats.innerText = seats;
    summaryUnitPrice.innerText = `$${rate.toFixed(2)} / month`;
    summaryTotal.innerText = `$${total.toFixed(2)} / month`;
  }

  // Listen for changes
  seatInput.addEventListener('input', updateSummary);
  updateSummary(); // Initialize

  // Render PayPal Buttons
  paypal.Buttons({
    createSubscription: function(data, actions) {
      const finalSeats = seatInput.value || '40';
      return actions.subscription.create({
        'plan_id': 'P-YOUR_PLAN_ID', // Swap with your actual Plan ID
        'quantity': finalSeats
      });
    },
    onApprove: function(data, actions) {
      alert('Subscription successfully started! ID: ' + data.subscriptionID);
    }
  }).render('#paypal-button-container');
</script>
"""
