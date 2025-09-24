const contenedor = document.getElementById('contenedor-vistas');

// ✅ Ya no cargamos secciones con fetch
// Solo aplicamos los estilos y eventos

// Asignar imágenes de fondo a las tarjetas dinámicamente
function aplicarFondosTarjetas() {
  document.querySelectorAll('.tarjeta[data-bg]').forEach(tarjeta => {
    const bg = tarjeta.getAttribute('data-bg');
    if (bg) {
      tarjeta.style.backgroundImage = `url(${bg})`;
    }
  });
}

function agregarEventoClick() {
  let indiceActual = 0;
  const vistas = document.querySelectorAll('.vista');
  const totalVistas = vistas.length;

  document.addEventListener('scroll', (e) => {
    const yClick = e.clientY;
    const alturaVentana = window.innerHeight;

    if (yClick < alturaVentana / 2) {
      indiceActual = Math.max(indiceActual - 1, 0);
    } else {
      indiceActual = Math.min(indiceActual + 1, totalVistas - 1);
    }

    vistas[indiceActual].scrollIntoView({ behavior: 'smooth' });
  });
}

function agregarEventosOpciones() {
  document.querySelectorAll('.tarjeta').forEach(tarjeta => {
    tarjeta.addEventListener('scroll', (e) => {
      e.stopPropagation();
      const target = document.querySelector(tarjeta.dataset.target);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

function actualizarVisible() {
  const vistas = document.querySelectorAll('.vista');
  const scrollTop = contenedor.scrollTop;
  const altura = window.innerHeight;

  vistas.forEach(vista => {
    const offsetTop = vista.offsetTop;
    if (scrollTop >= offsetTop - altura / 2 && scrollTop < offsetTop + altura / 2) {
      vista.classList.add('visible');
    } else {
      vista.classList.remove('visible');
    }
  });
}

// Detectar qué sección está visible al hacer scroll
contenedor.addEventListener('scroll', actualizarVisible);

// ✅ Inicialización (ya no hay fetch)
aplicarFondosTarjetas();
agregarEventoClick();
agregarEventosOpciones();
actualizarVisible();
