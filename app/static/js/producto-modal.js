/* Modal de producto: foto (ver/descargar) + precio en cuotas. Lo usan Stock y Consulta. */
(function () {
    const URL_IMG = "/stock/imagen/";
    const fmt = n => "$" + Number(n).toLocaleString("es-AR", {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const esc = t => String(t).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

    let modal = null;
    function crear() {
        modal = document.createElement("div");
        modal.className = "modal oculto";
        modal.innerHTML = '<div class="modal-contenido modal-producto"><div id="mp-cuerpo"></div></div>';
        modal.addEventListener("click", e => { if (e.target === modal) cerrar(); });
        document.body.appendChild(modal);
        document.addEventListener("keydown", e => { if (e.key === "Escape") cerrar(); });
    }
    function cerrar() { if (modal) modal.classList.add("oculto"); }

    window.abrirProducto = function (p) {
        if (!modal) crear();
        const c = p.cuotas;
        let html = '<h2 class="mp-titulo">' + esc(p.nombre) + '</h2>';
        if (p.tiene_imagen) {
            html += '<img class="mp-imagen" src="' + URL_IMG + p.id + '" alt="' + esc(p.nombre) + '">' +
                    '<a class="btn btn-chico" href="' + URL_IMG + p.id + '?descargar=1">Descargar imagen</a>';
        }
        html += '<div class="mp-precio">Precio de contado: <strong>' + fmt(p.precio_venta) + '</strong></div>';
        if (c) {
            html += '<div class="mp-cuotas"><h3>En cuotas</h3>' +
                '<div class="mp-fila"><span>Entrega</span><strong>' + fmt(c.entrega) + '</strong></div>' +
                '<div class="mp-fila"><span>' + c.cantidad + ' cuotas de</span><strong>' + fmt(c.cuota) + '</strong></div>' +
                '<div class="mp-fila mp-total"><span>Total financiado</span><strong>' + fmt(c.total) + '</strong></div>' +
                '<p class="mp-nota">La mitad se entrega al comprar; la otra mitad lleva ' + c.interes_pct + '% de interés (' + fmt(c.saldo_con_interes) + ') en ' + c.cantidad + ' cuotas.</p></div>';
        }
        html += '<div style="margin-top:14px"><button type="button" class="btn" id="mp-cerrar">Cerrar</button></div>';
        modal.querySelector("#mp-cuerpo").innerHTML = html;
        modal.querySelector("#mp-cerrar").addEventListener("click", cerrar);
        modal.classList.remove("oculto");
    };
})();
