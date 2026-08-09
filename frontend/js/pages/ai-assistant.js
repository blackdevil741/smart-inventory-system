/**
 * ai-assistant.js
 * Simple chat UI wired to the rule-based /api/ai-assistant/ask endpoint.
 */

firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await firebaseAuth.signOut();
  window.location.href = "./login.html";
});

const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function appendMessage(text, sender) {
  const el = document.createElement("div");
  el.className = `chat-message ${sender}`;
  el.textContent = text;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return el;
}

function appendTyping() {
  const el = document.createElement("div");
  el.className = "chat-typing";
  el.textContent = "Thinking...";
  el.id = "typingIndicator";
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function sendQuestion(question) {
  appendMessage(question, "user");
  chatInput.value = "";
  chatSendBtn.disabled = true;
  appendTyping();

  try {
    const result = await window.aiAssistantApi.ask(question);
    removeTyping();
    appendMessage(result.answer, "assistant");
  } catch (err) {
    removeTyping();
    appendMessage(`Sorry, something went wrong: ${err.message}`, "assistant");
  } finally {
    chatSendBtn.disabled = false;
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  sendQuestion(question);
});

document.querySelectorAll(".chat-suggestions button").forEach((button) => {
  button.addEventListener("click", () => {
    sendQuestion(button.dataset.question);
  });
});
