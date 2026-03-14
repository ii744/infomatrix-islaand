// Навігація між розділами
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        
        // Оновлення активних класів
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');
    });
});

// Перемикання калькуляторів
document.querySelectorAll('.calc-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const calcType = this.dataset.calc;
        
        document.querySelectorAll('.calc-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        document.querySelectorAll('.calculator').forEach(c => c.classList.remove('active'));
        document.getElementById(calcType + '-calc').classList.add('active');
    });
});

// Перемикання симуляторів
document.querySelectorAll('.sim-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const simType = this.dataset.sim;
        
        document.querySelectorAll('.sim-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        
        document.querySelectorAll('.simulator').forEach(s => s.classList.remove('active'));
        document.getElementById(simType + '-sim').classList.add('active');
    });
});

// Перемикання видимості поля k для комбінаторики
document.getElementById('combo-type').addEventListener('change', function() {
    const kInput = document.getElementById('k-input');
    kInput.style.display = this.value === 'permutation' ? 'none' : 'block';
});

// ========== КАЛЬКУЛЯТОРИ ==========

// Класична ймовірність
function calculateClassical() {
    const m = parseInt(document.getElementById('favorable').value);
    const n = parseInt(document.getElementById('total').value);
    
    if (n <= 0) {
        document.getElementById('classical-result').innerHTML = '❌ Помилка: n має бути більше 0';
        return;
    }
    
    if (m < 0 || m > n) {
        document.getElementById('classical-result').innerHTML = '❌ Помилка: m має бути від 0 до n';
        return;
    }
    
    const probability = m / n;
    const percentage = (probability * 100).toFixed(2);
    
    document.getElementById('classical-result').innerHTML = `
        <div>P(A) = ${m} / ${n} = <strong>${probability.toFixed(4)}</strong></div>
        <div style="font-size: 0.9em; margin-top: 10px;">або ${percentage}%</div>
    `;
}

// Комбінаторика
function factorial(n) {
    if (n === 0 || n === 1) return 1;
    let result = 1;
    for (let i = 2; i <= n; i++) result *= i;
    return result;
}

function calculateCombination() {
    const type = document.getElementById('combo-type').value;
    const n = parseInt(document.getElementById('combo-n').value);
    const k = parseInt(document.getElementById('combo-k').value);
    
    let result, formula, explanation;
    
    if (type === 'permutation') {
        result = factorial(n);
        formula = `P<sub>${n}</sub> = ${n}! = ${result.toLocaleString()}`;
        explanation = `Кількість перестановок з ${n} елементів`;
    } else if (type === 'arrangement') {
        if (k > n) {
            document.getElementById('combo-result').innerHTML = '❌ Помилка: k не може бути більше n';
            return;
        }
        result = factorial(n) / factorial(n - k);
        formula = `A<sub>${n}</sub><sup>${k}</sup> = ${n}! / ${n-k}! = ${result.toLocaleString()}`;
        explanation = `Кількість розміщень з ${n} по ${k}`;
    } else {
        if (k > n) {
            document.getElementById('combo-result').innerHTML = '❌ Помилка: k не може бути більше n';
            return;
        }
        result = factorial(n) / (factorial(k) * factorial(n - k));
        formula = `C<sub>${n}</sub><sup>${k}</sup> = ${n}! / (${k}! · ${n-k}!) = ${result.toLocaleString()}`;
        explanation = `Кількість сполучень з ${n} по ${k}`;
    }
    
    document.getElementById('combo-result').innerHTML = `
        <div>${formula}</div>
        <div style="font-size: 0.9em; margin-top: 10px;">${explanation}</div>
    `;
}

// Формула Байєса
function calculateBayes() {
    const hypProbs = document.querySelectorAll('.hyp-prob');
    const hypConditionals = document.querySelectorAll('.hyp-conditional');
    
    let totalProb = 0;
    const hypotheses = [];
    
    hypProbs.forEach((input, index) => {
        const prob = parseFloat(input.value);
        const conditional = parseFloat(hypConditionals[index].value);
        
        if (isNaN(prob) || isNaN(conditional)) {
            document.getElementById('bayes-result').innerHTML = '❌ Заповніть всі поля';
            return;
        }
        
        hypotheses.push({ prob, conditional, contribution: prob * conditional });
        totalProb += prob * conditional;
    });
    
    if (totalProb === 0) {
        document.getElementById('bayes-result').innerHTML = '❌ Неможлива подія А';
        return;
    }
    
    let resultHTML = `<div style="margin-bottom: 15px;">P(A) = ${totalProb.toFixed(4)}</div>`;
    
    hypotheses.forEach((hyp, index) => {
        const posteriorProb = hyp.contribution / totalProb;
        resultHTML += `
            <div style="margin: 8px 0; padding: 10px; background: rgba(255,255,255,0.2); border-radius: 8px;">
                P(H<sub>${index + 1}</sub>|A) = ${(posteriorProb * 100).toFixed(2)}%
            </div>
        `;
    });
    
    document.getElementById('bayes-result').innerHTML = resultHTML;
}

// ========== СИМУЛЯТОРИ ==========

// Монета
function simulateCoin() {
    const flips = parseInt(document.getElementById('coin-flips').value);
    const coin = document.getElementById('coin');
    
    // Анімація
    coin.classList.add('flipping');
    
    setTimeout(() => {
        coin.classList.remove('flipping');
        
        let heads = 0;
        let tails = 0;
        
        for (let i = 0; i < flips; i++) {
            Math.random() < 0.5 ? heads++ : tails++;
        }
        
        const headsPercent = ((heads / flips) * 100).toFixed(2);
        const tailsPercent = ((tails / flips) * 100).toFixed(2);
        
        // Останній результат
        const lastResult = Math.random() < 0.5;
        coin.style.transform = lastResult ? 'rotateY(0deg)' : 'rotateY(180deg)';
        
        document.getElementById('coin-result').innerHTML = `
            <div>Гербів: ${heads} (${headsPercent}%) | Цифр: ${tails} (${tailsPercent}%)</div>
            <div style="font-size: 0.9em; margin-top: 10px;">Теоретична ймовірність: 50% кожного</div>
        `;
        
        // Графік
        document.getElementById('coin-chart').innerHTML = `
            <h4 style="margin-bottom: 15px; color: #667eea;">📊 Результати симуляції</h4>
            <div class="bar-container">
                <div class="bar-item">
                    <div class="bar" style="height: ${headsPercent * 2}px;"></div>
                    <div class="bar-label">Герб</div>
                    <div class="bar-value">${headsPercent}%</div>
                </div>
                <div class="bar-item">
                    <div class="bar" style="height: ${tailsPercent * 2}px;"></div>
                    <div class="bar-label">Цифра</div>
                    <div class="bar-value">${tailsPercent}%</div>
                </div>
            </div>
        `;
    }, 1000);
}

// Кубик
const diceSymbols = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];

function simulateDice() {
    const rolls = parseInt(document.getElementById('dice-rolls').value);
    const dice = document.getElementById('dice');
    
    dice.classList.add('rolling');
    
    setTimeout(() => {
        dice.classList.remove('rolling');
        
        const results = [0, 0, 0, 0, 0, 0];
        
        for (let i = 0; i < rolls; i++) {
            const roll = Math.floor(Math.random() * 6);
            results[roll]++;
        }
        
        // Останній результат
        const lastRoll = Math.floor(Math.random() * 6);
        dice.textContent = diceSymbols[lastRoll];
        
        let resultHTML = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">';
        results.forEach((count, index) => {
            const percent = ((count / rolls) * 100).toFixed(1);
            resultHTML += `<div>${index + 1}: ${count} (${percent}%)</div>`;
        });
        resultHTML += '</div>';
        
        document.getElementById('dice-result').innerHTML = resultHTML;
        
        // Графік
        const maxCount = Math.max(...results);
        let chartHTML = '<h4 style="margin-bottom: 15px; color: #667eea;">📊 Розподіл результатів</h4>';
        chartHTML += '<div class="bar-container">';
        
        results.forEach((count, index) => {
            const height = (count / maxCount) * 150;
            const percent = ((count / rolls) * 100).toFixed(1);
            chartHTML += `
                <div class="bar-item">
                    <div class="bar" style="height: ${height}px;">${diceSymbols[index]}</div>
                    <div class="bar-label">${index + 1}</div>
                    <div class="bar-value">${percent}%</div>
                </div>
            `;
        });
        
        chartHTML += '</div>';
        document.getElementById('dice-chart').innerHTML = chartHTML;
    }, 500);
}

// Урна
function simulateUrn() {
    const white = parseInt(document.getElementById('white-balls').value);
    const black = parseInt(document.getElementById('black-balls').value);
    const drawCount = parseInt(document.getElementById('draw-count').value);
    const experiments = parseInt(document.getElementById('urn-experiments').value);
    
    const total = white + black;
    
    if (total === 0) {
        document.getElementById('urn-result').innerHTML = '❌ Додайте кульки в урну';
        return;
    }
    
    if (drawCount > total) {
        document.getElementById('urn-result').innerHTML = '❌ Не можна витягнути більше кульок, ніж є в урні';
        return;
    }
    
    // Результати: скільки білих кульок витягнуто
    const results = {};
    
    for (let exp = 0; exp < experiments; exp++) {
        let urn = [];
        for (let i = 0; i < white; i++) urn.push('W');
        for (let i = 0; i < black; i++) urn.push('B');
        
        let whiteDrawn = 0;
        for (let d = 0; d < drawCount; d++) {
            const index = Math.floor(Math.random() * urn.length);
            if (urn[index] === 'W') whiteDrawn++;
            urn.splice(index, 1);
        }
        
        results[whiteDrawn] = (results[whiteDrawn] || 0) + 1;
    }
    
    // Вивід результатів
    let resultHTML = `<div>Урна: ${white} білих, ${black} чорних</div>`;
    resultHTML += `<div>Витягуємо: ${drawCount} кульок</div>`;
    resultHTML += '<div style="margin-top: 15px;"><strong>Результати:</strong></div>';
    
    const sortedKeys = Object.keys(results).map(Number).sort((a, b) => a - b);
    sortedKeys.forEach(whiteCount => {
        const count = results[whiteCount];
        const percent = ((count / experiments) * 100).toFixed(1);
        resultHTML += `<div>${whiteCount} білих: ${count} (${percent}%)</div>`;
    });
    
    document.getElementById('urn-result').innerHTML = resultHTML;
    
    // Графік
    const maxCount = Math.max(...Object.values(results));
    let chartHTML = '<h4 style="margin-bottom: 15px; color: #667eea;">📊 Розподіл</h4>';
    chartHTML += '<div class="bar-container">';
    
    sortedKeys.forEach(whiteCount => {
        const count = results[whiteCount];
        const height = (count / maxCount) * 150;
        const percent = ((count / experiments) * 100).toFixed(1);
        
        chartHTML += `
            <div class="bar-item">
                <div class="bar" style="height: ${height}px;"></div>
                <div class="bar-label">${whiteCount}W</div>
                <div class="bar-value">${percent}%</div>
            </div>
        `;
    });
    
    chartHTML += '</div>';
    document.getElementById('urn-chart').innerHTML = chartHTML;
}

// ========== ТЕСТ ==========

const quizQuestions = [
    {
        question: "Яка ймовірність випадання герба при підкиданні правильної монети?",
        options: ["0", "0.25", "0.5", "1"],
        correct: 2,
        explanation: "Правильна монета має два рівноймовірні результати, тому P(герб) = 1/2 = 0.5"
    },
    {
        question: "Подія, яка обов'язково станеться, називається...",
        options: ["Неможливою", "Випадковою", "Достовірною", "Незалежною"],
        correct: 2,
        explanation: "Достовірна подія має ймовірність 1 і обов'язково станеться"
    },
    {
        question: "У скриньці 3 білі і 2 чорні кульки. Яка ймовірність витягнути білу?",
        options: ["2/5", "3/5", "1/2", "3/2"],
        correct: 1,
        explanation: "P(біла) = 3/(3+2) = 3/5"
    },
    {
        question: "Яка формула виражає класичну ймовірність?",
        options: ["P(A) = n/m", "P(A) = m/n", "P(A) = m+n", "P(A) = m·n"],
        correct: 1,
        explanation: "P(A) = m/n, де m - сприятливі результати, n - всі результати"
    },
    {
        question: "Сума ймовірностей всіх елементарних подій дорівнює...",
        options: ["0", "0.5", "1", "Залежить від експерименту"],
        correct: 2,
        explanation: "Сума ймовірностей всіх елементарних подій завжди дорівнює 1"
    }
];

let currentQuestion = 0;
let score = 0;
let answered = new Array(quizQuestions.length).fill(false);
let selectedAnswers = new Array(quizQuestions.length).fill(null);

function loadQuestion() {
    const q = quizQuestions[currentQuestion];
    document.getElementById('question-text').textContent = q.question;
    document.getElementById('current-q').textContent = currentQuestion + 1;
    document.getElementById('total-q').textContent = quizQuestions.length;
    
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    q.options.forEach((option, index) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.textContent = option;
        btn.onclick = () => selectOption(index);
        
        if (selectedAnswers[currentQuestion] === index) {
            btn.classList.add('selected');
        }
        
        if (answered[currentQuestion]) {
            btn.disabled = true;
            if (index === q.correct) {
                btn.classList.add('correct');
            } else if (selectedAnswers[currentQuestion] === index) {
                btn.classList.add('incorrect');
            }
        }
        
        optionsContainer.appendChild(btn);
    });
    
    // Кнопки навігації
    document.getElementById('prev-btn').disabled = currentQuestion === 0;
    document.getElementById('next-btn').textContent = 
        currentQuestion === quizQuestions.length - 1 ? 'Завершити' : 'Наступне →';
}

function selectOption(index) {
    if (answered[currentQuestion]) return;
    
    selectedAnswers[currentQuestion] = index;
    answered[currentQuestion] = true;
    
    if (index === quizQuestions[currentQuestion].correct) {
        score++;
    }
    
    loadQuestion();
    
    // Показуємо пояснення
    const explanation = document.createElement('div');
    explanation.className = 'example';
    explanation.style.marginTop = '20px';
    explanation.innerHTML = `<strong>Пояснення:</strong> ${quizQuestions[currentQuestion].explanation}`;
    document.getElementById('options-container').appendChild(explanation);
}

function nextQuestion() {
    if (currentQuestion < quizQuestions.length - 1) {
        currentQuestion++;
        loadQuestion();
    } else {
        showResults();
    }
}

function prevQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        loadQuestion();
    }
}

function showResults() {
    document.getElementById('question-container').style.display = 'none';
    document.getElementById('quiz-results').classList.remove('hidden');
    document.querySelector('.quiz-controls').style.display = 'none';
    
    const percentage = ((score / quizQuestions.length) * 100).toFixed(0);
    let message = '';
    
    if (percentage >= 80) {
        message = '🎉 Відмінно! Ви чудово знаєте теорію ймовірностей!';
    } else if (percentage >= 60) {
        message = '👍 Добре! Але є куди рости.';
    } else {
        message = '📚 Рекомендуємо повторити матеріал.';
    }
    
    document.getElementById('score').innerHTML = `
        <div>${score} з ${quizQuestions.length}</div>
        <div style="font-size: 0.7em; color: #667eea;">${percentage}%</div>
    `;
    
    document.querySelector('.quiz-results').innerHTML += `<p style="margin-top: 20px;">${message}</p>`;
}

function restartQuiz() {
    currentQuestion = 0;
    score = 0;
    answered = new Array(quizQuestions.length).fill(false);
    selectedAnswers = new Array(quizQuestions.length).fill(null);
    
    document.getElementById('question-container').style.display = 'block';
    document.getElementById('quiz-results').classList.add('hidden');
    document.querySelector('.quiz-controls').style.display = 'flex';
    
    document.querySelector('.quiz-results').innerHTML = `
        <h3>Результати тесту</h3>
        <div id="score"></div>
        <button class="quiz-btn restart-btn" onclick="restartQuiz()">Пройти знову</button>
    `;
    
    loadQuestion();
}

// Ініціалізація тесту при завантаженні
document.addEventListener('DOMContentLoaded', () => {
    loadQuestion();
});
