async function sendMove(direction) {
  const res = await fetch('/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ move: direction })
  });
  return res.json();
}

document.querySelectorAll('button[data-move]').forEach(btn => {
  btn.addEventListener('click', async () => {
    document.getElementById('message').textContent = '';
    const result = await sendMove(btn.dataset.move);
    if (!result.success) {
      document.getElementById('message').textContent = result.message;
    } else if (result.win) {
      document.getElementById('winbox').classList.remove('hidden');
      document.querySelector('.control-panel').classList.add('hidden');
      document.getElementById('message').textContent = 'ACCESS GRANTED! You reached the exit!';
    } else {
      document.getElementById('coords').textContent = `(${result.x},${result.y})`;
    }
  });
});

document.getElementById('submit').addEventListener('click', async () => {
  const code = document.getElementById('code').value;
  const res = await fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code })
  });
  const json = await res.json();
  const resultDiv = document.getElementById('result');
  if (json.success) {
    resultDiv.innerHTML = `<span style="color: var(--cyber-accent); text-shadow: 0 0 10px var(--cyber-accent);">🎉 FLAG: ${json.flag}</span>`;
  } else {
    resultDiv.innerHTML = `<span style="color: var(--cyber-danger); text-shadow: 0 0 10px var(--cyber-danger);">${json.message}</span>`;
  }
});

// Temporary test button to show submission panel
document.getElementById('test-submit').addEventListener('click', () => {
  document.getElementById('winbox').classList.remove('hidden');
  document.getElementById('message').textContent = 'Submission panel shown';
  // Scroll to the submission panel
  document.getElementById('winbox').scrollIntoView({ behavior: 'smooth' });
});