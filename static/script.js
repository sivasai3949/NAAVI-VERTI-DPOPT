const form = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const leftContainer = document.querySelector(".chat-container-left");
const rightContainer = document.querySelector(".chat-container-right");
const pathwayBtn = document.getElementById("pathway-btn");

let questionCounter = 1; // Initialize a counter for numbering questions

// Handle form submission
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userText = userInput.value.trim();
    if (!userText) return;

    // Add user input to the correct container
    const userBubble = document.createElement("div");
    userBubble.classList.add("chat-bubble", "user-bubble");
    userBubble.textContent = userText;

    // Determine current phase
    let currentPhase = document.querySelector(".active-container");
    if (!currentPhase) {
        // Default to the left container
        currentPhase = leftContainer;
    }
    currentPhase.appendChild(userBubble);

    userInput.value = "";

    // Send user input to the backend
    const formData = new FormData();
    formData.append("user_input", userText);

    const response = await fetch("/process_chat", {
        method: "POST",
        body: formData,
    });

    const data = await response.json();

    if (data.question) {
        // Add the chatbot's question to the correct container with numbering
        const botBubble = document.createElement("div");
        botBubble.classList.add("chat-bubble", "bot-bubble");
        botBubble.innerHTML = `<strong>${questionCounter}. </strong>${data.question}`; // Add numbering

        const targetContainer =
            data.container === "left" ? leftContainer : rightContainer;
        targetContainer.appendChild(botBubble);

        // Increment the question counter
        questionCounter++;

        // Update active container if needed
        if (data.container === "right") {
            document.querySelector(".active-container")?.classList.remove("active-container");
            rightContainer.classList.add("active-container");
        }
    }

    if (data.show_pathway_button) {
        pathwayBtn.style.display = "block";
    }

    if (data.pathway_response) {
        const pathways = data.pathway_response;

        // Clear the right container
        rightContainer.innerHTML = "";

        pathways.forEach((pathway, index) => {
            const pathwayCard = document.createElement("div");
            pathwayCard.classList.add("card", "pathway-card");

            const pathwayHeader = document.createElement("div");
            pathwayHeader.classList.add("card-header", "pathway-card-header");
            pathwayHeader.setAttribute("id", `heading${index + 1}`);

            const pathwayButton = document.createElement("button");
            pathwayButton.classList.add("btn", "btn-link");
            pathwayButton.setAttribute("data-toggle", "collapse");
            pathwayButton.setAttribute("data-target", `#collapse${index + 1}`);
            pathwayButton.setAttribute("aria-expanded", "true");
            pathwayButton.setAttribute("aria-controls", `collapse${index + 1}`);
            pathwayButton.textContent = pathway.title;

            pathwayHeader.appendChild(pathwayButton);
            pathwayCard.appendChild(pathwayHeader);

            const pathwayCollapse = document.createElement("div");
            pathwayCollapse.classList.add("collapse");
            pathwayCollapse.setAttribute("id", `collapse${index + 1}`);
            pathwayCollapse.setAttribute("aria-labelledby", `heading${index + 1}`);
            pathwayCollapse.setAttribute("data-parent", "#pathways");

            const pathwayBody = document.createElement("div");
            pathwayBody.classList.add("card-body");

            const pathwaySteps = document.createElement("ol");
            pathway.steps.forEach((step) => {
                const stepItem = document.createElement("li");
                stepItem.textContent = step;
                pathwaySteps.appendChild(stepItem);
            });

            pathwayBody.appendChild(pathwaySteps);

            if (pathway.description) {
                const detailsButton = document.createElement("button");
                detailsButton.classList.add("btn", "btn-info", "mt-3");
                detailsButton.textContent = "Show Details";
                detailsButton.addEventListener("click", () =>
                    toggleDetails(`details${index + 1}`)
                );

                const detailsDiv = document.createElement("div");
                detailsDiv.setAttribute("id", `details${index + 1}`);
                detailsDiv.classList.add("pathway-details");
                detailsDiv.innerHTML = `<p><strong>Description:</strong> ${pathway.description}</p>`;

                pathwayBody.appendChild(detailsButton);
                pathwayBody.appendChild(detailsDiv);
            }

            pathwayCollapse.appendChild(pathwayBody);
            pathwayCard.appendChild(pathwayCollapse);

            rightContainer.appendChild(pathwayCard);
        });

        pathwayBtn.classList.add("hidden");
    }
});

// Redirect to generate pathways page
pathwayBtn.addEventListener("click", () => {
    window.location.href = "/generate_pathway";
});

// Function to toggle the visibility of pathway details
function toggleDetails(id) {
    const detailsDiv = document.getElementById(id);
    detailsDiv.classList.toggle("show-details");
}
