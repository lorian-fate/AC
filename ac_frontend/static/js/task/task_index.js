

const dataAseguradoras = [
    {
        id: "mapfre",
        nombre: "Mapfre",
        color: "#d32f2f",
        tareas: [
            { id: 101, nombre: "Siniestro Hogar", desc: "Reportar rotura de tubería", tiempo: "15 min" },
            { id: 102, nombre: "Renovación Póliza", desc: "Actualizar datos anuales", tiempo: "5 min" },
            { id: 103, nombre: "Cotizar Comunidad", desc: "Cotizar seguro para comunidad", tiempo: "8 min" }
        ]
    },
    {
        id: "caser",
        nombre: "Caser",
        color: "#1976d2",
        tareas: [
            { id: 201, nombre: "Asistencia Médica", desc: "Solicitar cita especialista", tiempo: "10 min" },
            { id: 202, nombre: "Baja de Servicio", desc: "Procesar cancelación", tiempo: "20 min" }
        ]
    },
    {
        id: "dkv",
        nombre: "Dkv",
        color: "#388e3c",
        tareas: [
            { id: 301, nombre: "Reembolso Gastos", desc: "Subir facturas de farmacia", tiempo: "8 min" },
            { id: 302, nombre: "Autorización", desc: "Prueba diagnóstica compleja", tiempo: "12 min" }
        ]
    }
];

// Variables para el manejo del modal
let tareaPendiente = null;
const modal = document.getElementById('confirmModal');
const msgElem = document.getElementById('confirmMessage');

function renderInsurance() {
    const grid = document.getElementById('insuranceGrid');
    dataAseguradoras.forEach((aseg, index) => {
        const card = document.createElement('div');
        card.className = `insurance-card ${index === 0 ? 'active' : ''}`;
        card.style.borderLeft = `6px solid ${aseg.color}`;
        card.innerHTML = `<h3>${aseg.nombre}</h3><p>${aseg.tareas.length} Tareas</p>`;
        card.onclick = () => {
            document.querySelectorAll('.insurance-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            renderTasks(aseg.id);
        };
        grid.appendChild(card);
    });
}

function renderTasks(idAseguradora) {
    const aseg = dataAseguradoras.find(a => a.id === idAseguradora);
    const tbody = document.getElementById('tasksBody');
    document.getElementById('selectedInsuranceTitle').textContent = `Tareas de ${aseg.nombre}`;
    
    tbody.innerHTML = '';
    aseg.tareas.forEach(tarea => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="bold">${tarea.nombre}</td>
            <td>${tarea.desc}</td>
            <td><span class="badge">${tarea.tiempo}</span></td>
            <td>
                <button class="btn-execute" onclick="pedirConfirmacion('${tarea.nombre}')">
                    Ejecutar
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Función que abre el DIV en lugar de alert
function pedirConfirmacion(nombreTarea) {
    tareaPendiente = nombreTarea;
    msgElem.textContent = `¿Seguro desea ejecutar la tarea: ${nombreTarea}?`;
    modal.classList.add('show');
}

// Lógica de los botones del modal
document.getElementById('closeModalBtn').onclick = () => {
    modal.classList.remove('show');
    tareaPendiente = null;
};

document.getElementById('confirmActionBtn').onclick = () => {
    if (tareaPendiente) {
        console.log(`Ejecutando: ${tareaPendiente}`);
        alert(`¡Iniciando proceso para ${tareaPendiente}!`); // Solo para feedback, puedes quitarlo
        modal.classList.remove('show');
        tareaPendiente = null;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    renderInsurance();
    renderTasks(dataAseguradoras[0].id);
});