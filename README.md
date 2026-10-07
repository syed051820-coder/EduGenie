<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EduGenie</title>
  <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
  <main class="wrap">
    <h1>EduGenie</h1>
    <p class="tagline">Google Gemini Powered Learning Assistant</p>

    <form id="ask-form">
      <textarea id="question" placeholder="Ask me anything you want to learn..." required></textarea>
      <button type="submit">Ask</button>
    </form>

    <div id="answer" class="answer hidden"></div>
    <p id="status" class="status"></p>
  </main>

  <script src="/static/script.js"></script>
</body>
</html>