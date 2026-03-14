const API_URL = "http://127.0.0.1:8000";

document.addEventListener('DOMContentLoaded', () => {
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

    const feedContainer = document.getElementById('feed-container');
    const token = localStorage.getItem('token'); 
    if (window.location.pathname.includes('index-main.html') && !token) {
        alert("Будь ласка, увійдіть у систему!");
        window.location.href = "index.html";
    }


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
                                <p class="mb-1"><strong>Час:</strong> ${req.time_cost} год.</p>
                                <p class="mb-2"><strong>Локація:</strong> ${req.location} | <strong>Тег:</strong> ${req.category}</p>
                                <button class="btn btn-dark fw-bold" onclick="alert('а')">Відгукнутися</button>
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

    const myRequestsList = document.getElementById('my-requests-list');
    
    if (window.location.pathname.includes('profile.html')) {
        if (!token) {
            alert("Будь ласка, увійдіть у систему!");
            window.location.href = "index.html";
        }

        async function loadProfile() {
            try {
                const [meRes, statsRes, requestsRes] = await Promise.all([
                    fetch(`${API_URL}/me`, { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch(`${API_URL}/stats`, { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch(`${API_URL}/users/me/requests`, { headers: { 'Authorization': `Bearer ${token}` } })
                ]);

                if (!meRes.ok) throw new Error("Помилка авторизації");

                const user = await meRes.json();
                const stats = await statsRes.json();
                const requests = await requestsRes.json();
                document.getElementById('profile-name').innerText = `${user.first_name} ${user.last_name}`;
                document.getElementById('profile-location').innerText = user.location;
                document.getElementById('hours-earned').innerText = stats.total_earned;
                document.getElementById('hours-spent').innerText = stats.total_spent;
                myRequestsList.innerHTML = '';
                
                if (requests.length === 0) {
                    myRequestsList.innerHTML = '<p class="text-center">У вас ще немає створених запитів.</p>';
                }

                requests.forEach(req => {
                    let statusText = "Очікує";
                    if (req.status === "in_progress") statusText = "В роботі";
                    if (req.status === "completed") statusText = "Виконано";

                    myRequestsList.innerHTML += `
                        <div class="card request-card shadow-sm">
                            <p class="text-muted mb-2">${statusText}</p>
                            <div class="request-box">
                                <p class="mb-0 fw-bold">${req.title}</p>
                                <p class="mb-2" style="font-size: 0.9rem;">${req.description}</p>
                                <small class="text-muted">По часу близько ${req.time_cost} годин.</small>
                            </div>
                            <div class="text-center">
                                <button class="btn btn-custom btn-sm">Деталі</button>
                            </div>
                        </div>
                    `;
                });
            } catch (err) {
                console.error(err);
                alert("Не вдалося завантажити профіль.");
            }
        }

        loadProfile();
        document.getElementById('btn-create-request').addEventListener('click', () => {
            window.location.href = "index-requests.html";
        });
    }
    const createRequestForm = document.querySelector('form');
    const titleInput = document.querySelector('input[placeholder="Назва запиту"]');

    if (window.location.pathname.includes('index-requests.html') && createRequestForm && titleInput) {
        if (!token) {
            alert("Будь ласка, увійдіть у систему!");
            window.location.href = "index.html";
        }

        createRequestForm.addEventListener('submit', async (event) => {
            event.preventDefault(); 

            const errorBox = document.getElementById('error-box');
            errorBox.style.display = 'none';
            const showError = (msg) => {
                errorBox.innerText = msg;
                errorBox.style.display = 'block';
            };

            const hoursInput = document.querySelector('input[placeholder="Кількість годин"]');
            const locationInput = document.querySelector('input[placeholder="Локація"]');
            const categorySelect = document.querySelector('select');
            const descInput = document.querySelector('textarea[placeholder="Опис запиту"]');

            if (!titleInput.value || !hoursInput.value || parseInt(hoursInput.value) <= 0 || !locationInput.value || categorySelect.value === "Категорія") {
                showError("Будь ласка, заповніть усі поля та оберіть категорію!");
                return;
            }

            const newRequest = {
                title: titleInput.value,
                description: descInput.value, 
                time_cost: parseInt(hoursInput.value),
                location: locationInput.value,
                category: categorySelect.value 
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
                    window.location.href = "index-main.html"; 
                } else {
                    const err = await response.json();
                    
                    if (Array.isArray(err.detail)) {
                        const messages = err.detail.map(e => e.msg).join(", ");
                        showError("Помилка даних: " + messages);
                    } else {
                        showError("Помилка: " + err.detail);
                    }
                }
            } catch (err) {
                console.error(err);
                showError("Не вдалося підключитися до сервера. Перевірте з'єднання.");
            }
        });
    }
});