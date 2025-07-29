// DOM Elements
const chatBody = document.getElementById("chat-body");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const loading = document.getElementById("loading");
const apiKeyModal = document.getElementById("api-key-modal");
const settingsBtn = document.getElementById("settings-btn");
const submitApiKeyBtn = document.getElementById("submit-api-key");
const apiKeyInput = document.getElementById("api-key-input");

// Quick reply options
const quickReplyOptions = {
  welcome: [
    { text: "Universities", action: "List of all universities" },
    {
      text: "GPA requirements",
      action: "What are the GPA requirements for different universities?",
    },
    {
      text: "Required documents",
      action: "What documents do I need for admission?",
    },
    {
      text: "Contact information",
      action: "Give me contact information for universities",
    },
  ],
  universities: [
    { text: "List of all universities", action: "List of all universities" },
    {
      text: "Public or private universities",
      action: "What are the public and private universities in Kuwait?",
    },
    {
      text: "GPA requirements",
      action: "GPA requirements for science or arts programs",
    },
    {
      text: "Search by location",
      action: "Search for universities by location",
    },
  ],
};

// Focus input on page load if API key is set
window.onload = () => {
  if (apiKeyModal.style.display === "none") {
    userInput.focus();
  } else {
    apiKeyInput.focus();
  }
};

// Settings button click event
settingsBtn.addEventListener("click", () => {
  apiKeyModal.style.display = "flex";
});

// Submit API key
submitApiKeyBtn.addEventListener("click", () => {
  const apiKey = apiKeyInput.value.trim();
  if (apiKey) {
    fetch("/set-api-key", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        apiKey: apiKey,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          apiKeyModal.style.display = "none";
          userInput.focus();
          // Add a message to inform user
          addBotMessage(
            "API key set successfully! You can now ask questions.",
            "welcome"
          );
        } else {
          alert("Failed to set API key: " + data.error);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred while setting the API key.");
      });
  } else {
    alert("Please enter a valid API key.");
  }
});

// Adjust textarea height based on content
userInput.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height =
    (this.scrollHeight > 32 ? Math.min(this.scrollHeight, 152) : 32) + "px";
});

// Send message when button is clicked
sendBtn.addEventListener("click", sendMessage);

// Send message when Enter key is pressed (without shift)
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// API key input Enter key press
apiKeyInput.addEventListener("keyup", (e) => {
  if (e.key === "Enter") {
    submitApiKeyBtn.click();
  }
});

/**
 * Handles quick reply button clicks
 * @param {string} action - The action to perform
 */
function handleQuickReply(action) {
  userInput.value = action;
  sendMessage();
}

/**
 * Sends the user message to the server and handles the response
 */
function sendMessage() {
  const message = userInput.value.trim();
  if (message === "") return;

  // Add user message to chat
  addUserMessage(message);

  // Clear input and reset height
  userInput.value = "";
  userInput.style.height = "32px";

  // Show loading indicator
  loading.style.display = "block";
  chatBody.scrollTop = chatBody.scrollHeight;

  // Send message to API
  fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      // Hide loading indicator
      loading.style.display = "none";

      // Determine which quick reply set to use
      let quickReplySet = "universities";
      if (
        message.toLowerCase().includes("welcome") ||
        message.toLowerCase().includes("hello") ||
        message.toLowerCase().includes("hi")
      ) {
        quickReplySet = "welcome";
      }

      // Add bot response to chat
      addBotMessage(data.response, quickReplySet);

      // If response indicates API key issue, show modal
      if (
        data.response.includes("OpenAI API key not provided") ||
        (data.response.includes("Error:") && data.response.includes("API key"))
      ) {
        apiKeyModal.style.display = "flex";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      loading.style.display = "none";
      addBotMessage(
        "Sorry, there was an error processing your request. Please try again later.",
        "welcome"
      );
    });
}

/**
 * Adds a user message to the chat
 * @param {string} message - The user's message text
 */
function addUserMessage(message) {
  const messageElement = document.createElement("div");
  messageElement.className = "aral";
  messageElement.innerHTML = `
    <div class="arpal">
      <div class="arpt internormalwhite20px">${message}</div>
    </div>
    <div style="align-items: center; background-color: var(--black); border-radius: 22px; display: flex; height: 44px; width: 44px; justify-content: center;">
      <i class="fas fa-user" style="color: white;"></i>
    </div>
  `;

  insertBeforeLoadingIndicator(messageElement);
  chatBody.scrollTop = chatBody.scrollHeight;
}

/**
 * Adds a bot message to the chat
 * @param {string} message - The bot's message text (may contain markdown)
 * @param {string} quickReplySet - The set of quick replies to show (welcome, universities)
 */
function addBotMessage(message, quickReplySet = "welcome") {
  const messageElement = document.createElement("div");
  messageElement.className = "ural";

  // Process markdown
  const processedMessage = marked.parse(message);

  // Build the message HTML with bot icon and speech bubble
  let messageHTML = `
    <div class="urpal">
      <div class="urpf">
        <i class="fas fa-robot urpi"></i>
      </div>
    </div>
    <div class="urtal">
      <div class="urt internormalwhite20px">${processedMessage}</div>
  `;

  // Add quick reply buttons if we have them for this type
  if (quickReplyOptions[quickReplySet]) {
    messageHTML += `<div class="quick-reply-container">`;
    quickReplyOptions[quickReplySet].forEach((option) => {
      messageHTML += `<button class="quick-reply-btn" onclick="handleQuickReply('${option.action}')">${option.text}</button>`;
    });
    messageHTML += `</div>`;
  }

  // Close the container div
  messageHTML += `</div>`;

  messageElement.innerHTML = messageHTML;

  insertBeforeLoadingIndicator(messageElement);
  chatBody.scrollTop = chatBody.scrollHeight;
}

/**
 * Helper function to insert an element before the loading indicator
 * @param {HTMLElement} element - The element to insert
 */
function insertBeforeLoadingIndicator(element) {
  chatBody.insertBefore(element, loading);
}
