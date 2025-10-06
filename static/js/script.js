

// Solo fondo de tarjetas dinámico si aplica (puedes eliminar si no usas data-bg)
function aplicarFondosTarjetas() {
  document.querySelectorAll('.tarjeta[data-bg]').forEach(tarjeta => {
    const bg = tarjeta.getAttribute('data-bg');
    if (bg) {
      tarjeta.style.backgroundImage = `url(${bg})`;
    }
  });
}

aplicarFondosTarjetas();
