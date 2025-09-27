
// Funcionalidad para marcar tareas como completadas - ejemplo sencillo
document.querySelectorAll('.btn-action').forEach(button => {
button.addEventListener('click', () => {
    const row = button.closest('tr');
    const statusSpan = row.querySelector('.status');
    
    // Solo actuar si no está completada ya
    if(!button.disabled){
    statusSpan.textContent = 'Completado';
    statusSpan.classList.remove('pending', 'in-progress');
    statusSpan.classList.add('completed');
    statusSpan.setAttribute('aria-label', 'Completado');
    button.textContent = 'Completado';
    button.disabled = true;

    // Actualizar indicadores de resumen
    updateSummary();
    }
});
});

function updateSummary(){
const totalFincas = 14; // fijo por demo
const completedTasks = document.querySelectorAll('.status.completed').length;
const pendingTasks = document.querySelectorAll('.status.pending').length;
const inProgressTasks = document.querySelectorAll('.status.in-progress').length;

document.getElementById('totalFincas').textContent = totalFincas;
document.getElementById('completedTasks').textContent = completedTasks;
document.getElementById('pendingTasks').textContent = pendingTasks;
document.getElementById('inProgressTasks').textContent = inProgressTasks;
}

// Se actualizan automáticamente al cargar
updateSummary();


document.querySelector('.btn-logout').addEventListener('click', () => {
    // Redirigir al endpoint de logout de Flask
    window.location.href = '/logout';

});

