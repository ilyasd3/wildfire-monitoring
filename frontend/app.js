document.getElementById('subscriptionForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const zipCode = document.getElementById('zipCode').value;
    const email = document.getElementById('email').value;
    const subscribeButton = document.querySelector('button[type="submit"]');
    const resetButton = document.getElementById('resetButton');

    // Show loading state
    subscribeButton.textContent = 'Subscribing...';
    subscribeButton.disabled = true;
    subscribeButton.classList.add('loading');

    try {
        const response = await fetch('https://0c92hj1w8e.execute-api.us-east-1.amazonaws.com/prod/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                zip_code: zipCode,
                email: email
            })
        });

        if (!response.ok) {
            // Attempt to parse error response as JSON
            let errorMessage = 'Subscription failed. Please try again.';
            try {
                const errorData = await response.json();
                console.error('Error response from server:', errorData);
                errorMessage = errorData.error || errorMessage;
            } catch (jsonError) {
                console.error('Failed to parse error response as JSON', jsonError);
            }
            throw new Error(errorMessage);
        }

        // Parse successful response as JSON
        const responseData = await response.json();
        console.log('Server response:', responseData);

        // On successful subscription
        subscribeButton.textContent = 'Subscribed ✓';
        subscribeButton.classList.add('subscribed');
        resetButton.style.display = 'block'; // Show the reset button

    } catch (error) {
        console.error('Subscription failed:', error);
        subscribeButton.textContent = 'Try Again';
        subscribeButton.classList.remove('subscribed');
        subscribeButton.disabled = false; // Re-enable the button to try again
        alert(error.message);
    } finally {
        subscribeButton.classList.remove('loading');
    }
});

// Reset form to allow a new submission
document.getElementById('resetButton').addEventListener('click', function() {
    const subscribeButton = document.querySelector('button[type="submit"]');
    const resetButton = document.getElementById('resetButton');
    const form = document.getElementById('subscriptionForm');

    form.reset(); // Clear the form inputs
    subscribeButton.textContent = 'Subscribe';
    subscribeButton.classList.remove('subscribed');
    subscribeButton.disabled = false;
    resetButton.style.display = 'none'; // Hide the reset button
});
