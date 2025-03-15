document.getElementById('subscriptionForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const zipCode = document.getElementById('zipCode').value;
    const email = document.getElementById('email').value;
    const subscribeButton = document.querySelector('button[type="submit"]');
    const resetButton = document.getElementById('resetButton');

    // Shows subscription loading
    subscribeButton.textContent = 'Subscribing...';
    subscribeButton.disabled = true;
    subscribeButton.classList.add('loading');

    try {
        const response = await fetch('https://0c92hj1w8e.execute-api.us-east-1.amazonaws.com/prod/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ zip_code: zipCode, email: email })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Subscription failed. Please try again.');
        }

        const data = await response.json();
        console.log('Success:', data);

        subscribeButton.textContent = 'Subscribed ✔';
        subscribeButton.classList.add('subscribed');
        resetButton.style.display = 'block';

    } catch (error) {
        console.error('Error:', error);
        subscribeButton.textContent = 'Try Again';
        subscribeButton.classList.remove('subscribed');
        subscribeButton.disabled = false;
        alert(error.message);
    } finally {
        subscribeButton.classList.remove('loading');
    }
});

// Resets the form if clicked
document.getElementById('resetButton').addEventListener('click', function() {
    const form = document.getElementById('subscriptionForm');
    const subscribeButton = document.querySelector('button[type="submit"]');
    const resetButton = document.getElementById('resetButton');

    form.reset();
    subscribeButton.textContent = 'Subscribe';
    subscribeButton.classList.remove('subscribed');
    subscribeButton.disabled = false;
    resetButton.style.display = 'none';
});
