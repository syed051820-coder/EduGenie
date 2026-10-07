const form = document.getElementById("ask-form");
const questionEl = document.getElementById("question");
const answerEl = document.getElementById("answer");
const statusEl = document.getElementById("status");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = questionEl.value.trim();
  if (!question) return;

  const button = form.querySelector("button");
  button.disabled = true;
  statusEl.textContent = "Thinking...";
  answerEl.classList.add("hidden");

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Request failed");
    }

    answerEl.textContent = data.answer;
    answerEl.classList.remove("hidden");
    statusEl.textContent = data.demo_mode ? "Running in demo mode." : "";
  } catch (err) {
    answerEl.textContent = `Error: ${err.message}`;
    answerEl.classList.remove("hidden");
    statusEl.textContent = "";
  } finally {
    button.disabled = false;
  }
});