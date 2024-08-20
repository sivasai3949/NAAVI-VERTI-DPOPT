document.getElementById('send-btn').addEventListener('click', function(event) {
    event.preventDefault();
    sendUserInput();
});

document.getElementById('user-input').addEventListener('keypress', function(event) {
    if (event.keyCode === 13 && !event.shiftKey) {
        event.preventDefault();
        sendUserInput();
    }
});

document.getElementById('pathway-btn').addEventListener('click', function(event) {
    event.preventDefault();
    createPathway();
});

// Theme toggle functionality
document.getElementById('theme-toggle').addEventListener('change', function() {
    document.body.classList.toggle('dark-mode');
});

function sendUserInput() {
    var userInput = document.getElementById('user-input').value;
    if (!userInput.trim()) return;

    showLoading(); // Show loading indicator

    fetch('/process_chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'user_input=' + encodeURIComponent(userInput)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(); // Hide loading indicator
        if (data.error) {
            appendChat("robot", "Error: " + data.error);
        } else {
            appendChat("user", userInput);
            if (data.response) {
                appendChat("robot", data.response);
                triggerConfetti(); // Trigger confetti when response is received
            }
            if (data.question) {
                appendChat("robot", data.question);
            }
            if (data.show_pathway_button) {
                document.getElementById('pathway-btn').classList.remove('hidden');
            } else {
                document.getElementById('pathway-btn').classList.add('hidden');
            }
        }
    })
    .catch(error => {
        hideLoading(); // Hide loading indicator
        console.error('Error:', error);
    });
}

function createPathway() {
    window.open('/generate_pathway', '_blank');
}

function appendChat(role, message) {
    var chatContainer = document.getElementById('chat-container');
    var chatBubble = document.createElement('div');
    chatBubble.classList.add('chat-bubble');
    chatBubble.classList.add(role + '-bubble');
    chatBubble.innerText = message;

    chatContainer.appendChild(chatBubble);
    document.getElementById('user-input').value = ''; // Clear input field after sending
    chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to bottom of chat
}

function showLoading() {
    var chatContainer = document.getElementById('chat-container');
    var loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'loading-indicator';
    loadingIndicator.classList.add('chat-bubble', 'robot-bubble');
    loadingIndicator.innerText = '...'; // Loading dots
    chatContainer.appendChild(loadingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to bottom of chat
}

function hideLoading() {
    var loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

function triggerConfetti() {
    var end = Date.now() + (2 * 1000); // Confetti duration: 2 seconds
    var colors = ['#bb0000', '#ffffff'];

    function frame() {
        confetti({
            particleCount: 2,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: colors
        });
        confetti({
            particleCount: 2,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: colors
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    }

    frame();
}
