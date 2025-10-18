const form = document.getElementById('registerForm');
const formMessage = document.getElementById('formMessage');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Ocultar mensajes previos
    formMessage.textContent = '';
    const usuario = form.usuario.value.trim();
    const correo = form.correo.value.trim();
    const password = form.password.value;

    // Validaciones básicas en frontend
    let valid = true;

    if (!usuario) {
    document.getElementById('usuarioError').style.display = 'block';
    valid = false;
    } else {
    document.getElementById('usuarioError').style.display = 'none';
    }

    if (!correo || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo)) {
    document.getElementById('correoError').style.display = 'block';
    valid = false;
    } else {
    document.getElementById('correoError').style.display = 'none';
    }

    if (!password || password.length < 6) {
    document.getElementById('passwordError').style.display = 'block';
    valid = false;
    } else {
    document.getElementById('passwordError').style.display = 'none';
    }

    if (!valid) return;

    try {
    const response = await fetch('api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario, correo, password })
    });

    const result = await response.json();

    if (response.ok) {
        formMessage.style.color = 'green';
        formMessage.textContent = result.message;
        form.reset();
    } else {
        formMessage.style.color = 'red';
        formMessage.textContent = result.message || 'Error desconocido';
    }
    } catch (error) {
    formMessage.style.color = 'red';
    formMessage.textContent = 'Error de conexión';
    }
});