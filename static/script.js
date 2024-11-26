const form = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const leftContainer = document.querySelector(".chat-container-left");
const rightContainer = document.querySelector(".chat-container-right");
const pathwayBtn = document.getElementById("pathway-btn");

// Handle form submission
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userText = userInput.value.trim();
    if (!userText) return;

    // Add user input to the correct container
    const userBubble = document.createElement("div");
    userBubble.classList.add("chat-bubble", "user-bubble");
    userBubble.textContent = userText;

    let currentPhase = document.querySelector(".active-container");
    if (!currentPhase) {
        // If no active container is found, default to the left container
        currentPhase = leftContainer; 
    }
    currentPhase.appendChild(userBubble);

    userInput.value = "";

    // Send user input to the backend
    const response = await fetch("/process_chat", {
        method: "POST",
        body: new URLSearchParams({ user_input: userText }),
    });

    const data = await response.json();

    if (data.question) {
        // Add the chatbot's question to the correct container
        const botBubble = document.createElement("div");
        botBubble.classList.add("chat-bubble", "bot-bubble");
        botBubble.textContent = data.question;

        if (data.container === "left") {
            leftContainer.appendChild(botBubble);
        } else if (data.container === "right") {
            rightContainer.appendChild(botBubble);
        }

        // Switch active container if needed
        if (data.container === "right") {
            document.querySelector(".active-container").classList.remove("active-container");
            rightContainer.classList.add("active-container");
        }
    } else if (data.response) {
        // Show the final message and pathway button
        const finalMessage = document.createElement("div");
        finalMessage.classList.add("chat-bubble", "bot-bubble");
        finalMessage.textContent = data.response;

        rightContainer.appendChild(finalMessage);
        pathwayBtn.classList.remove("hidden");
    }
});

// Redirect to generate pathways
pathwayBtn.addEventListener("click", () => {
    window.location.href = "/generate_pathway";
});
