// =========================================
// ELEMENTS
// =========================================

const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const predictBtn = document.getElementById("predictBtn");
const statusText = document.getElementById("statusText");
const resultBox = document.getElementById("result");

const patientName = document.getElementById("patientName");
const patientAge = document.getElementById("patientAge");
const patientGender = document.getElementById("patientGender");
const patientContact = document.getElementById("patientContact");

let selectedFile = null;

// -----------------------------
// Chat state (per prediction)
// -----------------------------

let chatHistory = [];
let currentDisease = null;
let currentConfidenceValue = null;

// =========================================
// DISEASE INFO (fallback only, used if Gemini
// explanation is missing/empty)
// =========================================

const DISEASE_INFO = {
    "Acne": "Acne is a common inflammatory skin condition that occurs when hair follicles become clogged with oil and dead skin cells. Common features: pimples, clogged pores, redness and inflammation.",
    "Eczema": "Eczema is a condition that can make the skin dry, itchy and inflamed. Common features: itching, dryness, redness, scaling and irritation.",
    "Vitiligo": "Vitiligo is a condition in which areas of the skin lose pigment, producing lighter patches. Common features: clearly lighter patches with loss of normal skin pigment."
};

// =========================================
// IMAGE SELECT + PREVIEW
// =========================================

imageInput.addEventListener("change", () => {

    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    selectedFile = file;

    const reader = new FileReader();

    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.classList.remove("hidden");
    };

    reader.readAsDataURL(file);

    // Hide the dashed upload box once an image is chosen
    const uploadLabel = document.querySelector(".upload-label");
    if (uploadLabel) {
        uploadLabel.classList.add("hidden");
    }

    predictBtn.disabled = false;
    statusText.textContent = "";
});

// =========================================
// SMALL HELPER: escape text before inserting
// into innerHTML (basic XSS safety since we
// render user-entered patient info + model
// output directly into the DOM)
// =========================================

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

// =========================================
// PREDICT BUTTON CLICK
// =========================================

predictBtn.addEventListener("click", async () => {

    // -----------------------------
    // Basic validation
    // -----------------------------

    if (!selectedFile) {
        statusText.textContent = "Please choose an image first.";
        return;
    }

    if (!patientName.value || !patientAge.value || !patientGender.value) {
        statusText.textContent = "Please fill in patient information first.";
        return;
    }

    // -----------------------------
    // Build form data (patient info + image)
    // -----------------------------

    const formData = new FormData();

    formData.append("name", patientName.value);
    formData.append("age", patientAge.value);
    formData.append("gender", patientGender.value);
    formData.append("contact", patientContact.value || "");
    formData.append("image", selectedFile);

    // -----------------------------
    // UI: loading state (styled)
    // -----------------------------

    predictBtn.disabled = true;
    statusText.textContent = "";

    resultBox.innerHTML = `
        <div class="loading-result">
            <div class="loader"></div>
            <h3>Analyzing image...</h3>
            <p>Please wait while the AI model processes the image.</p>
        </div>
    `;

    try {

        const response = await fetch("/predict", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.detail) {

            resultBox.innerHTML = `
                <div class="error-result">
                    <div class="error-icon">!</div>
                    <h3>Prediction Failed</h3>
                    <p>${escapeHtml(data.detail)}</p>
                    <button class="btn analyze-again" onclick="location.reload()">Try Again</button>
                </div>
            `;

            predictBtn.disabled = false;
            return;
        }

        // -----------------------------
        // Show result (professional layout)
        // -----------------------------

        // Prefer the Gemini-generated explanation coming back from
        // the backend. Fall back to the static local description
        // only if the AI explanation is missing for some reason.
        const explanation = data.explanation || DISEASE_INFO[data.prediction] || "No additional information available.";
        const confidenceValue = parseFloat(data.confidence);

        // Reset chat state for this new prediction
        chatHistory = [];
        currentDisease = data.prediction;
        currentConfidenceValue = confidenceValue;

        resultBox.innerHTML = `
            <div class="professional-result">

                <div class="success-icon">✓</div>

                <p class="result-label">PREDICTION RESULT</p>

                <h2 class="disease-name">${escapeHtml(data.prediction)}</h2>

                <div class="confidence-section">
                    <div class="confidence-header">
                        <span>Confidence Score</span>
                        <strong>${escapeHtml(data.confidence)}</strong>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidenceValue}%"></div>
                    </div>
                </div>

                <div class="disease-info">
                    <h3>About ${escapeHtml(data.prediction)}</h3>
                    <p class="ai-explanation">${escapeHtml(explanation).replace(/\n/g, "<br>")}</p>
                    <p><strong>Patient:</strong> ${escapeHtml(patientName.value)}, ${escapeHtml(patientAge.value)} yrs, ${escapeHtml(patientGender.value)}</p>
                    <p><strong>Record ID:</strong> ${escapeHtml(data.id)}</p>
                </div>

                <div class="medical-disclaimer">
                    <strong>Important</strong>
                    <p>This AI prediction is for educational purposes only and is not a medical diagnosis. Please consult a qualified healthcare professional for concerning skin changes.</p>
                </div>

                <div class="chat-section">
                    <h3>Ask about your result</h3>
                    <p class="chat-hint">Chat with the AI assistant about ${escapeHtml(data.prediction)}.</p>

                    <div id="chatMessages" class="chat-messages"></div>

                    <div class="chat-input-row">
                        <input
                            type="text"
                            id="chatInput"
                            class="chat-input"
                            placeholder="Type a question..."
                        >
                        <button id="chatSendBtn" class="btn chat-send-btn">Send</button>
                    </div>
                </div>

                <button class="analyze-again" onclick="location.reload()">Analyze Another Image</button>

            </div>
        `;

        statusText.textContent = "";

        setupChat();

    } catch (error) {

        resultBox.innerHTML = `
            <div class="error-result">
                <div class="error-icon">!</div>
                <h3>Something Went Wrong</h3>
                <p>${escapeHtml(error.message)}</p>
                <button class="btn analyze-again" onclick="location.reload()">Try Again</button>
            </div>
        `;

    } finally {

        predictBtn.disabled = false;

    }
});

// =========================================
// CHATBOT (ChatGPT-style follow-up chat
// about the current prediction)
// =========================================

function renderChatMessages() {

    const chatMessagesBox = document.getElementById("chatMessages");

    if (!chatMessagesBox) {
        return;
    }

    chatMessagesBox.innerHTML = chatHistory.map((turn) => {

        const bubbleClass = turn.role === "user" ? "chat-bubble user" : "chat-bubble assistant";

        return `<div class="${bubbleClass}">${escapeHtml(turn.content).replace(/\n/g, "<br>")}</div>`;

    }).join("");

    // Auto-scroll to the latest message
    chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;
}

function setupChat() {

    const chatInput = document.getElementById("chatInput");
    const chatSendBtn = document.getElementById("chatSendBtn");

    if (!chatInput || !chatSendBtn) {
        return;
    }

    const send = () => sendChatMessage();

    chatSendBtn.addEventListener("click", send);

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            send();
        }
    });

    renderChatMessages();
}

async function sendChatMessage() {

    const chatInput = document.getElementById("chatInput");
    const chatSendBtn = document.getElementById("chatSendBtn");

    if (!chatInput) {
        return;
    }

    const userMessage = chatInput.value.trim();

    if (!userMessage) {
        return;
    }

    if (!currentDisease) {
        return;
    }

    // Add user message immediately
    chatHistory.push({ role: "user", content: userMessage });
    renderChatMessages();

    chatInput.value = "";
    chatInput.disabled = true;
    chatSendBtn.disabled = true;

    // Typing indicator
    chatHistory.push({ role: "assistant", content: "Typing..." });
    renderChatMessages();

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                disease: currentDisease,
                confidence: currentConfidenceValue,
                history: chatHistory.slice(0, -2), // exclude this turn's placeholder + user msg duplicate logic below
                message: userMessage
            })
        });

        const data = await response.json();

        // Remove the "Typing..." placeholder
        chatHistory.pop();

        if (data.detail) {
            chatHistory.push({ role: "assistant", content: `Sorry, something went wrong: ${data.detail}` });
        } else {
            chatHistory.push({ role: "assistant", content: data.reply });
        }

    } catch (error) {

        chatHistory.pop();
        chatHistory.push({ role: "assistant", content: `Sorry, something went wrong: ${error.message}` });

    } finally {

        renderChatMessages();
        chatInput.disabled = false;
        chatSendBtn.disabled = false;
        chatInput.focus();

    }
}