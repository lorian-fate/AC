
const modal = document.getElementById('modal');
const fincaForm = document.getElementById('fincaForm');
const fincasBody = document.getElementById('fincasBody');
const createFincaBtn = document.getElementById('createFincaBtn');
const cancelBtn = document.getElementById('cancelBtn');
const modalTitle = document.getElementById('modalTitle');
const fincaIdInput = document.getElementById('fincaId');

// Escapar texto para evitar XSS
function escapeHtml(text) {
if (!text) return '';
return text.replace(/[&<>"']/g, function(m) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]);
});
}

async function loadFincas() {
const res = await fetch('/api/fincas');
const fincas = await res.json();
fincasBody.innerHTML = '';
fincas.forEach(finca => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
    <td>${escapeHtml(finca.nombre)}</td>
    <td>${escapeHtml(finca.direccion || '')}</td>
    <td>${escapeHtml(finca.descripcion || '')}</td>
    <td>${escapeHtml(finca.responsable || '')}</td>
    <td>
        <button class="action-btn edit-btn" data-id="${finca.id}" aria-label="Editar finca ${escapeHtml(finca.nombre)}">Editar</button>
        <button class="action-btn delete-btn" data-id="${finca.id}" aria-label="Eliminar finca ${escapeHtml(finca.nombre)}">Eliminar</button>
    </td>
    `;
    fincasBody.appendChild(tr);
});
}

function openModal(edit = false, finca = null) {
modal.classList.add('active');
if (edit && finca) {
    modalTitle.textContent = 'Editar Finca';
    fincaIdInput.value = finca.id;
    fincaForm.nombre.value = finca.nombre;
    fincaForm.direccion.value = finca.direccion || '';
    fincaForm.descripcion.value = finca.descripcion || '';
    fincaForm.responsable.value = finca.responsable || '';
} else {
    modalTitle.textContent = 'Crear Finca';
    fincaIdInput.value = '';
    fincaForm.reset();
}
fincaForm.nombre.focus();
}

function closeModal() {
modal.classList.remove('active');
}

createFincaBtn.addEventListener('click', () => openModal());

cancelBtn.addEventListener('click', closeModal);

fincaForm.addEventListener('submit', async e => {
e.preventDefault();

const id = fincaIdInput.value;
const data = {
    nombre: fincaForm.nombre.value.trim(),
    direccion: fincaForm.direccion.value.trim(),
    descripcion: fincaForm.descripcion.value.trim(),
    responsable: fincaForm.responsable.value.trim()
};

if (!data.nombre) {
    alert('El nombre es obligatorio.');
    return;
}

let url = '/api/fincas';
let method = 'POST';
if (id) {
    url += `/${id}`;
    method = 'PUT';
}

const res = await fetch(url, {
    method,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
});
const result = await res.json();

const fincaMessage = document.getElementById('fincaMessage');
if (result.success) {
    closeModal();
    loadFincas();
    fincaMessage.textContent = result.message || 'Finca creada correctamente.';
    fincaMessage.style.color = 'green';
    setTimeout(() => { fincaMessage.textContent = ''; }, 3000);
} else {
    fincaMessage.textContent = result.message || 'Error al guardar la finca.';
    fincaMessage.style.color = 'red';
    setTimeout(() => { fincaMessage.textContent = ''; }, 3000);
}
});

fincasBody.addEventListener('click', async e => {
if (e.target.classList.contains('edit-btn')) {
    const id = e.target.dataset.id;
    const res = await fetch('/api/fincas');
    const fincas = await res.json();
    const finca = fincas.find(f => f.id == id);
    if (finca) openModal(true, finca);
} else if (e.target.classList.contains('delete-btn')) {
    const id = e.target.dataset.id;
    if (confirm('¿Estás seguro de eliminar esta finca?')) {
    const res = await fetch(`/api/fincas/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.success) {
        loadFincas();
    } else {
        alert(result.message || 'Error al eliminar la finca.');
    }
    }
}
});

// Carga inicial
loadFincas();
