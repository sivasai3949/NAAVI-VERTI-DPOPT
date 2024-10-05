let messageCount = 0; // Initialize a counter for user messages

document.getElementById("send-btn").addEventListener("click", function (event) {
  event.preventDefault();
  sendUserInput();
});

document
  .getElementById("user-input")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendUserInput();
    }
  });

document
  .getElementById("pathway-btn")
  .addEventListener("click", function (event) {
    event.preventDefault();
    createPathway();
  });

// Theme toggle functionality
document.getElementById("theme-toggle").addEventListener("change", function () {
  document.body.classList.toggle("dark-mode");
});

function sendUserInput() {
  const userInput = document.getElementById("user-input").value.trim();
  if (!userInput) return;

  showLoading();
  fetch("/process_chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `user_input=${encodeURIComponent(userInput)}`,
  })
    .then((response) => response.json())
    .then((data) => {
      hideLoading();
      if (data.error) {
        appendChat("robot", `Error: ${data.error}`);
      } else {
        appendChat("user", userInput);
        messageCount++; // Increment the message count for each valid user input

        if (data.response) {
          appendChat("robot", data.response);
          triggerConfetti();
        }
        if (data.question) {
          appendChat("robot", data.question);
        }

        // Enable the pathway button if message count reaches 5
        if (messageCount === 5) {
          const pathwayBtn = document.getElementById("pathway-btn");
          pathwayBtn.disabled = false; // Enable the button
        }
      }
    })
    .catch((error) => {
      hideLoading();
      console.error("Error:", error);
    });
}

function createPathway() {
  window.open("/generate_pathway", "_blank");
}

function appendChat(role, message) {
  const chatContainer = document.getElementById("chat-container");
  const chatBubble = document.createElement("div");
  chatBubble.classList.add("chat-bubble", `${role}-bubble`);
  chatBubble.innerText = message;
  chatContainer.appendChild(chatBubble);
  document.getElementById("user-input").value = ""; // Clear input field after sending
  chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to bottom of chat
}

function showLoading() {
  const chatContainer = document.getElementById("chat-container");
  const loadingIndicator = document.createElement("div");
  loadingIndicator.id = "loading-indicator";
  loadingIndicator.classList.add("chat-bubble", "robot-bubble");
  loadingIndicator.innerText = "..."; // Loading dots
  chatContainer.appendChild(loadingIndicator);
  chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to bottom of chat
}

function hideLoading() {
  const loadingIndicator = document.getElementById("loading-indicator");
  if (loadingIndicator) {
    loadingIndicator.remove();
  }
}

function triggerConfetti() {
  const end = Date.now() + 2000; // Confetti duration: 2 seconds
  const colors = ["#bb0000", "#ffffff"];
  function frame() {
    confetti({
      particleCount: 2,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors: colors,
    });
    confetti({
      particleCount: 2,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors: colors,
    });
    if (Date.now() < end) {
      requestAnimationFrame(frame);
    }
  }
  frame();
}
