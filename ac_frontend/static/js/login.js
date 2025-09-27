const form = document.getElementById('loginForm');
const emailInput = form.email;
const passwordInput = form.password;
const togglePasswordBtn = document.querySelector('.toggle-password');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');

togglePasswordBtn.addEventListener('click', () => {
    if(passwordInput.type === 'password'){
        passwordInput.type = 'text';
        togglePasswordBtn.textContent = '🙈';
    } else {
        passwordInput.type = 'password';
        togglePasswordBtn.textContent = '👁️';
    }
    passwordInput.focus();
});

form.addEventListener('submit', async e => {
    e.preventDefault();

    let valid = true;

    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value.trim())) {
        emailError.style.display = 'block';
        valid = false;
    } else emailError.style.display = 'none';

    if(passwordInput.value.trim().length < 6) {
        passwordError.style.display = 'block';
        valid = false;
    } else passwordError.style.display = 'none';

    if(!valid) return;

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: emailInput.value.trim(),
                password: passwordInput.value.trim()
            })
        });
        const data = await res.json();
        if(data.success){
            window.location.href = "/dashboard";  // redirigir al dashboard
        } else {
            alert(data.message);
        }
    } catch(err) {
        alert("Error del servidor");
        console.error(err);
    }
});
