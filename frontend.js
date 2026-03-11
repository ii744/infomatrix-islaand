// Головна адреса твого бекенду (тепер вона доступна всюди!)
const API_URL = "http://127.0.0.1:8000";

document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. ЛОГІКА РЕЄСТРАЦІЇ (index-regist.html)
    // ==========================================
    const registerForm = document.querySelector('form');
    const firstNameInput = document.querySelector('input[placeholder="Ім’я"]');
    
    if (registerForm && firstNameInput) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            
            const lastNameInput = document.querySelector('input[placeholder="Прізвище"]');
            const emailInput = document.querySelector('input[placeholder="Адреса електронної пошти"]');
            const passwordInput = document.querySelector('input[placeholder="Пароль"]');
            
            const userData = {
                email: emailInput.value,
                password: passwordInput.value,
                first_name: firstNameInput.value,
                last_name: lastNameInput.value,
                location: "Вінниця" 
            };

            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const result = await response.json();
                if (response.ok) {
                    alert("Ура! " + result.message);
                    window.location.href = "index.html"; 
                } else {
                    alert("Помилка: " + result.detail);
                }
            } catch (error) {
                console.error(error);
                alert("Помилка підключення до сервера!");
            }
        });
    }

    // ==========================================
    // 2. ЛОГІКА ЛОГІНУ (index.html)
    // ==========================================
    const loginEmailInput = document.querySelector('input[placeholder="Ім’я або адреса електронної пошти"]');

    if (registerForm && loginEmailInput) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const passwordInput = document.querySelector('input[placeholder="Пароль"]');
            
            const formData = new URLSearchParams();
            formData.append('username', loginEmailInput.value);
            formData.append('password', passwordInput.value);

            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });

                const result = await response.json();
                if (response.ok) {
                    localStorage.setItem('token', result.access_token);
                    alert("Успішний вхід!");
                    window.location.href = "index-main.html"; 
                } else {
                    alert("Помилка: Неправильний email або пароль");
                }
            } catch (error) {
                console.error(error);
                alert("Помилка підключення до сервера!");
            }
        });
    }

    // ==========================================
    // 3. ГОЛОВНА СТОРІНКА (index-main.html)
    // ==========================================
    const feedContainer = document.getElementById('feed-container');
    const token = localStorage.getItem('token'); 

    // Якщо ми на головній сторінці, але токена немає — виганяємо на логін
    if (window.location.pathname.includes('index-main.html') && !token) {
        alert("Будь ласка, увійдіть у систему!");
        window.location.href = "index.html";
    }

    // --- КНОПКА: МІЙ АКАУНТ ---
    const btnProfile = document.getElementById('btn-profile');
    if (btnProfile) {
        btnProfile.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch(`${API_URL}/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (response.ok) {
                    const user = await response.json();
                    alert(`Привіт, ${user.first_name}!\nТвій баланс: ${user.balance} годин.\nЛокація: ${user.location}`);
                } else {
                    alert("Помилка авторизації. Треба перезайти.");
                    localStorage.removeItem('token');
                    window.location.href = "index.html";
                }
            } catch (err) {
                console.error(err);
            }
        });
    }

    // --- КНОПКА: ОСТАННІ ЗАПИТИ (СТРІЧКА) ---
    const btnLatest = document.getElementById('btn-latest');
    if (btnLatest && feedContainer) {
        btnLatest.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_URL}/requests`); 
                const requests = await response.json();
                
                feedContainer.innerHTML = '<h3 style="font-family: \'El Messiri\';">Стрічка завдань:</h3>';
                
                if (requests.length === 0) {
                    feedContainer.innerHTML += '<p>Поки що завдань немає. Будь першим!</p>';
                }

                requests.forEach(req => {
                    feedContainer.innerHTML += `
                        <div class="card mt-3 shadow" style="border: 1px solid #494949;">
                            <div class="card-body">
                                <h4 class="card-title fw-bold" style="font-family: 'El Messiri';">${req.title}</h4>
                                <p class="card-text">${req.description}</p>
                                <hr>
                                <p class="mb-1"><strong>💰 Оплата:</strong> ${req.time_cost} год.</p>
                                <p class="mb-2"><strong>📍 Локація:</strong> ${req.location} | <strong>Тег:</strong> ${req.category}</p>
                                <button class="btn btn-dark fw-bold" onclick="alert('Функція відгуку в розробці!')">Відгукнутися</button>
                            </div>
                        </div>
                    `;
                });
            } catch (err) {
                console.error(err);
                alert("Не вдалося завантажити стрічку.");
            }
        });
    }

    // --- КНОПКА: СТВОРИТИ ЗАПИТ ---
    const btnCreate = document.getElementById('btn-create');
    if (btnCreate) {
        btnCreate.addEventListener('click', async () => {
            const title = prompt("Що потрібно зробити? (Наприклад: Погуляти з собакою)");
            if (!title) return;
            const desc = prompt("Детальний опис:");
            const hours = prompt("Скільки годин ти пропонуєш за це?");
            
            const newRequest = {
                title: title,
                description: desc,
                time_cost: parseInt(hours),
                location: "Вінниця", 
                category: "Допомога"
            };

            try {
                const response = await fetch(`${API_URL}/requests`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}` 
                    },
                    body: JSON.stringify(newRequest)
                });

                if (response.ok) {
                    alert("Завдання успішно створено!");
                    if(btnLatest) btnLatest.click(); // Оновлюємо стрічку
                } else {
                    const err = await response.json();
                    alert("Помилка: " + err.detail); 
                }
            } catch (err) {
                console.error(err);
            }
        });
    }
});