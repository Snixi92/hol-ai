let board = ['', '', '', '', '', '', '', '', ''];
let currentPlayer = 'X';
let gameActive = true;
const winningConditions = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];
const statusDisplay = document.getElementById('status');
const playerDisplay = document.getElementById('current-player');
const cells = document.querySelectorAll('.cell');

function handleCellClick(e) {
  const cell = e.target;
  const index = parseInt(cell.getAttribute('data-index'));
  if (board[index] !== '' || !gameActive) return;

  board[index] = currentPlayer;
  cell.textContent = currentPlayer;
  cell.classList.add(currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink');

  checkResult();
}

function checkResult() {
  let roundWon = false;
  for (let condition of winningConditions) {
    let a = board[condition[0]];
    let b = board[condition[1]];
    let c = board[condition[2]];
    if (a === '' || b === '' || c === '') continue;
    if (a === b && b === c) { roundWon = true; break; }
  }

  if (roundWon) {
    statusDisplay.innerHTML = `<span class="${currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink'}">${currentPlayer} A GAGNÉ ! 🎉</span>`;
    gameActive = false;
    return;
  }

  if (!board.includes('')) {
    statusDisplay.innerHTML = '<span class="neon-cyan">MATCH NUL ! 🤝</span>';
    gameActive = false;
    return;
  }

  currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
  playerDisplay.textContent = currentPlayer;
  playerDisplay.className = currentPlayer === 'X' ? 'neon-cyan' : 'neon-pink';
}

function resetGame() {
  board = ['', '', '', '', '', '', '', '', ''];
  currentPlayer = 'X';
  gameActive = true;
  statusDisplay.innerHTML = 'Tour du joueur : <span id="current-player" class="neon-cyan">X</span>';
  cells.forEach(cell => { cell.textContent = ''; cell.className = 'cell'; });
}

cells.forEach(c => c.addEventListener('click', handleCellClick));
document.getElementById('reset-btn').addEventListener('click', resetGame);