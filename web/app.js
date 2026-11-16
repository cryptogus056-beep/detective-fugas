/* Detective de Fugas Pyme: pagina de demostracion.
 *
 * Privacidad: esta pagina solo DESCARGA cosas (el motor Pyodide desde su CDN oficial y
 * archivos propios del sitio). Nunca envia nada: los archivos que eliges se leen en la
 * memoria de tu navegador y ahi se quedan.
 */
"use strict";

const PYODIDE_VERSION = "314.0.8";
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";
const NO_USAR = "ignorar";

const $ = (id) => document.getElementById(id);
const estado = { motor: null, roles: [], archivos: new Map(), xlsx: false, manifiesto: null, ultimo: null, reconocidos: [] };

function avisar(donde, texto, esError) {
  const p = $(donde);
  p.textContent = texto || "";
  p.classList.toggle("error", Boolean(esError));
}

async function traerTexto(ruta) {
  const r = await fetch(ruta, { cache: "no-cache" });
  if (!r.ok) throw new Error("No pude cargar " + ruta + " (" + r.status + ")");
  return r.text();
}

async function traerBytes(ruta) {
  const r = await fetch(ruta, { cache: "no-cache" });
  if (!r.ok) throw new Error("No pude cargar " + ruta + " (" + r.status + ")");
  return new Uint8Array(await r.arrayBuffer());
}

function cargarScript(url) {
  return new Promise((resolver, rechazar) => {
    const s = document.createElement("script");
    s.src = url;
    s.onload = resolver;
    s.onerror = () => rechazar(new Error("No pude descargar el motor de cálculo. Revisa tu conexión y recarga la página."));
    document.head.appendChild(s);
  });
}

function crearCarpetas(fs, ruta) {
  let actual = "";
  for (const parte of ruta.split("/").filter(Boolean)) {
    actual += "/" + parte;
    if (!fs.analyzePath(actual).exists) fs.mkdir(actual);
  }
}

/* Carga el motor una sola vez: Pyodide, el paquete detective/, las plantillas y (si se puede) el lector de Excel. */
function motor(donde) {
  if (!estado.motor) {
    estado.motor = (async () => {
      avisar(donde, "Cargando el motor de cálculo (unos 15 MB, solo la primera vez)...");
      if (!estado.manifiesto) estado.manifiesto = JSON.parse(await traerTexto("py/manifiesto.json"));
      await cargarScript(PYODIDE_URL + "pyodide.js");
      const py = await globalThis.loadPyodide({ indexURL: PYODIDE_URL });
      avisar(donde, "Preparando el detective...");
      crearCarpetas(py.FS, "/app/detective/reglas");
      crearCarpetas(py.FS, "/app/plantillas");
      crearCarpetas(py.FS, "/entrada");
      await Promise.all(estado.manifiesto.codigo.map(async (ruta) => {
        py.FS.writeFile("/app/" + ruta, await traerBytes("py/" + ruta));
      }));
      py.FS.writeFile("/app/puente.py", await traerBytes("puente.py"));
      if (estado.manifiesto.xlsx) {
        try {
          py.unpackArchive(await traerBytes("vendor/openpyxl.zip"), "zip", { extractDir: "/app" });
        } catch (error) {
          console.warn("Sin lector de Excel:", error);
        }
      }
      py.runPython("import sys\nsys.path.insert(0, '/app')\nimport puente");
      try {
        py.runPython("import openpyxl");
        estado.xlsx = true;
      } catch (error) {
        estado.xlsx = false;
      }
      estado.roles = JSON.parse(py.runPython("puente.roles()"));
      return py;
    })();
    estado.motor.catch(() => { estado.motor = null; });
  }
  return estado.motor;
}

function vaciarEntrada(py) {
  for (const nombre of py.FS.readdir("/entrada")) {
    if (nombre !== "." && nombre !== "..") py.FS.unlink("/entrada/" + nombre);
  }
}

function escribirEntrada(py, archivos, extra) {
  vaciarEntrada(py);
  for (const [nombre, bytes] of archivos) py.FS.writeFile("/entrada/" + nombre, bytes);
  for (const [nombre, texto] of Object.entries(extra || {})) py.FS.writeFile("/entrada/" + nombre, texto);
}

function tieneConfig() {
  return Array.from(estado.archivos.keys()).some((n) => n.toLowerCase() === "config.json");
}

/* Si no subieron config.json, se arma uno con lo que la persona escribio en la pagina. */
function configEscrita() {
  if (tieneConfig()) return {};
  const datos = {};
  if ($("empresa").value.trim()) datos.empresa = $("empresa").value.trim();
  if ($("corte").value) { datos.fecha_corte = $("corte").value; datos.periodo_hasta = $("corte").value; }
  return Object.keys(datos).length ? { "config.json": JSON.stringify(datos) } : {};
}

function ejecutar(py, funcion, ...argumentos) {
  const f = py.globals.get("puente")[funcion];
  try {
    return JSON.parse(f(...argumentos));
  } finally {
    f.destroy();
  }
}

/* ---------------------------------------------------------------- guia de archivos */

/* Que archivo sirve para que, donde se consigue y si hay planilla para llenar. */
const GUIA_ARCHIVOS = [
  {
    rol: "banco", titulo: "Cartola del banco", prioridad: "imprescindible", etiqueta: "Imprescindible",
    para: "Es la base: ahí se ve toda la plata que entra y sale. Con ella encuentro ingresos sin boleta, facturas que no te pagaron y software que pagas de más.",
    pasos: [
      "Entra al sitio web de tu banco para empresas o personas.",
      "Busca la opción \"Cartola\" o \"Movimientos\" de tu cuenta corriente o cuenta vista [sin verificar].",
      "Elige los últimos 3 meses y descarga en Excel o CSV [sin verificar].",
      "Si solo te dan PDF, pídele a tu ejecutivo la cartola en Excel: el PDF no sirve.",
    ],
  },
  {
    rol: "rcv_ventas", titulo: "Registro de Ventas del SII", prioridad: "muy", etiqueta: "Muy recomendado",
    para: "Es la lista de todas las facturas y boletas que emitiste. Sin él no puedo saber qué ventas tienen documento: lo necesito para 4 de los 5 tipos de fuga.",
    pasos: [
      "Entra a sii.cl con el RUT y la clave de tu empresa.",
      "En Servicios online busca \"Registro de Compras y Ventas\" [sin verificar].",
      "Elige el mes, entra a Ventas y descarga el detalle [sin verificar].",
      "Repite para cada mes. Puedes subir los 3 archivos: los sumo solo.",
    ],
  },
  {
    rol: "pos", titulo: "Ventas con tarjeta", prioridad: "recomendado", etiqueta: "Si vendes con tarjeta",
    para: "Mercado Pago, Transbank u otra máquina de tarjetas. Encuentro ventas con tarjeta a las que les faltó la boleta.",
    pasos: [
      "Entra al portal de tu máquina de tarjetas o de tu link de pago.",
      "Busca \"Reportes\" o \"Ventas\" [sin verificar].",
      "Descarga las ventas de los mismos meses en Excel o CSV [sin verificar].",
    ],
  },
  {
    rol: "cotizaciones", titulo: "Cotizaciones o presupuestos", prioridad: "recomendado", etiqueta: "Si cotizas",
    para: "Encuentro trabajos que el cliente aceptó y nadie facturó, y facturas que salieron por el neto en vez del total.",
    pasos: [
      "Si llevas tus cotizaciones en Excel, súbelo tal cual. Necesita: número, fecha, cliente, RUT, neto, estado y fecha de aceptación.",
      "Si no tienes planilla o tiene otras columnas, descarga la planilla para llenar y copia ahí las cotizaciones de los últimos meses.",
      "Estado: escribe Aceptada, Rechazada o Pendiente. Si solo sabes el neto, deja IVA y Total vacíos: los calculo yo.",
    ],
    planilla: "cotizaciones.csv",
    ejemplo: [["N Cotizacion", "Fecha", "Cliente", "RUT", "Servicio", "Neto", "IVA", "Total", "Estado", "Fecha aceptacion"],
              ["C-101", "01/09/2026", "Panadería Los Robles", "76.123.456-0", "Mantención", "100000", "", "", "Aceptada", "03/09/2026"]],
  },
  {
    rol: "rcv_compras", titulo: "Registro de Compras del SII", prioridad: "opcional", etiqueta: "Opcional",
    para: "Me ayuda a reconocer devoluciones de tus proveedores, para no confundirlas con ventas.",
    pasos: ["Está en el mismo lugar que el Registro de Ventas, en la parte de Compras [sin verificar]."],
  },
  {
    rol: "licencias", titulo: "Licencias de software", prioridad: "opcional", etiqueta: "Opcional",
    para: "Encuentro suscripciones que te cobran dos veces y licencias de personas que ya no trabajan contigo. Es un ahorro de todos los meses.",
    pasos: [
      "Casi nadie tiene este archivo: descarga la planilla para llenar.",
      "Anota una fila por cada usuario de cada programa que pagas (correo, diseño, contabilidad, almacenamiento...).",
      "Escribe el nombre del servicio como aparece en tu cartola, por ejemplo \"Canva Pro\" o \"Google Workspace\".",
      "Costo mensual en pesos. Estado: Activa o Cancelada.",
    ],
    planilla: "licencias.csv",
    ejemplo: [["Servicio", "Usuario o correo", "Plan", "Costo mensual", "Estado"],
              ["Google Workspace", "ana@tuempresa.cl", "Business Starter", "8600", "Activa"]],
  },
  {
    rol: "equipo", titulo: "Personas del equipo", prioridad: "opcional", etiqueta: "Opcional (va con licencias)",
    para: "Junto con las licencias, encuentro cuentas de software de personas que ya se fueron.",
    pasos: [
      "Descarga la planilla para llenar.",
      "Anota a cada persona con el mismo correo que usa en las licencias.",
      "Estado: Activo o Inactivo. Si se fue, anota la fecha de salida (por ejemplo 31/07/2026).",
    ],
    planilla: "equipo.csv",
    ejemplo: [["Nombre", "Correo", "Cargo", "Estado", "Fecha de ingreso", "Fecha de salida"],
              ["Bruno Vera", "bruno@tuempresa.cl", "Técnico", "Inactivo", "01/02/2022", "31/07/2026"]],
  },
];

/* Cada fuga necesita ciertos archivos: cada grupo interno se cumple con cualquiera de sus opciones. */
const COBERTURA = [
  { nombre: "Trabajo aceptado que nunca se facturó", necesita: [["cotizaciones"], ["rcv_ventas"]] },
  { nombre: "Factura que no te han pagado", necesita: [["rcv_ventas"], ["banco"]] },
  { nombre: "Plata que entró sin boleta ni factura", necesita: [["rcv_ventas"], ["banco", "pos"]] },
  { nombre: "Software que pagas de más", necesita: [["banco"], ["licencias"]], mejora: "equipo" },
  { nombre: "IVA que salió de tu bolsillo", necesita: [["rcv_ventas"]] },
];

function titulo(rol) {
  const g = GUIA_ARCHIVOS.find((x) => x.rol === rol);
  return g ? g.titulo : rol;
}

function crear(etiqueta, clase, texto) {
  const e = document.createElement(etiqueta);
  if (clase) e.className = clase;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function pintarListaArchivos() {
  const lista = $("lista-archivos");
  lista.textContent = "";
  for (const g of GUIA_ARCHIVOS) {
    const tarjeta = crear("details", "tarjeta prioridad-" + g.prioridad);
    tarjeta.id = "tarjeta-" + g.rol;
    const resumen = crear("summary");
    const cabeza = crear("span", "tarjeta-cabeza");
    cabeza.append(crear("span", "tarjeta-titulo", g.titulo), crear("span", "insignia", g.etiqueta));
    resumen.append(cabeza, crear("span", "tarjeta-estado", "Falta"), crear("span", "tarjeta-para", g.para));
    tarjeta.appendChild(resumen);
    const cuerpo = crear("div", "tarjeta-cuerpo");
    cuerpo.appendChild(crear("strong", "", "Cómo conseguirlo"));
    const ol = crear("ol");
    for (const paso of g.pasos) ol.appendChild(crear("li", "", paso));
    cuerpo.appendChild(ol);
    if (g.planilla) {
      const a = crear("a", "boton secundario", "Descargar planilla para llenar");
      a.href = "llenar/" + g.planilla;
      a.download = g.planilla;
      cuerpo.appendChild(a);
    }
    if (g.ejemplo) {
      cuerpo.appendChild(crear("p", "nota", "Así se ve una fila llena (deja la primera fila, la de los títulos, tal cual):"));
      const caja = crear("div", "tabla-scroll");
      const tabla = crear("table", "ejemplo");
      g.ejemplo.forEach((fila, i) => {
        const tr = crear("tr");
        for (const celda of fila) tr.appendChild(crear(i === 0 ? "th" : "td", "", celda));
        tabla.appendChild(tr);
      });
      caja.appendChild(tabla);
      cuerpo.appendChild(caja);
    }
    tarjeta.appendChild(cuerpo);
    lista.appendChild(tarjeta);
  }
}

/* Que rol tiene hoy cada archivo, segun lo reconocido y lo que la persona eligio en la lista. */
function archivosPorRol() {
  const porRol = {};
  for (const select of $("tabla-archivos").querySelectorAll("select")) {
    if (select.value === NO_USAR) continue;
    const r = estado.reconocidos.find((x) => x.nombre === select.dataset.archivo);
    (porRol[select.value] = porRol[select.value] || []).push({ nombre: select.dataset.archivo, filas: r ? r.filas : null });
  }
  return porRol;
}

function actualizarGuia() {
  const porRol = archivosPorRol();
  for (const g of GUIA_ARCHIVOS) {
    const tarjeta = $("tarjeta-" + g.rol);
    const archivos = porRol[g.rol] || [];
    tarjeta.classList.toggle("listo", archivos.length > 0);
    tarjeta.querySelector(".tarjeta-estado").textContent = archivos.length
      ? "Listo: " + archivos.map((a) => a.nombre + (a.filas !== null && a.filas !== undefined ? " (" + a.filas + " filas)" : "")).join(", ")
      : "Falta";
  }
  const caja = $("cobertura");
  caja.textContent = "";
  const tiene = (rol) => (porRol[rol] || []).length > 0;
  let cubiertas = 0;
  const ul = crear("ul");
  for (const f of COBERTURA) {
    const faltan = f.necesita.filter((grupo) => !grupo.some(tiene));
    const ok = faltan.length === 0;
    if (ok) cubiertas += 1;
    const li = crear("li", ok ? "si" : "no");
    li.appendChild(crear("span", "marca", ok ? "Sí" : "No"));
    li.appendChild(crear("span", "", f.nombre));
    if (!ok) {
      li.appendChild(crear("small", "", "Falta: " + faltan.map((grupo) => grupo.map(titulo).join(" o ")).join(" y ")));
    } else if (f.mejora && !tiene(f.mejora)) {
      li.appendChild(crear("small", "", "Con " + titulo(f.mejora).toLowerCase() + " también reviso licencias de personas que ya se fueron"));
    }
    ul.appendChild(li);
  }
  const h = crear("strong", "", "Qué puedo revisar con lo que subiste: " + cubiertas + " de " + COBERTURA.length + " tipos de fuga");
  caja.append(h, ul);
  caja.classList.toggle("completa", cubiertas === COBERTURA.length);
}

function etapa(n) {
  [1, 2, 3].forEach((i) => {
    const li = $("etapa-" + i);
    li.classList.toggle("hecho", i < n);
    li.classList.toggle("actual", i === n);
  });
}

/* ---------------------------------------------------------------- resultado (ejemplo y propio) */

const GUIA_LECTURA = [
  ["Plan de acción", "Qué hacer y en qué orden, agrupado: cobrar, regularizar boletas, cortar software y revisar el IVA."],
  ["Resumen en 5 líneas", "Al comienzo del informe: cuánta plata hay en juego, qué encontré y qué hacer primero esta semana."],
  ["Tabla de fugas", "Ordenada de la más cara a la más barata. \"Plata en juego\" es lo que pierdes o te deben. Si \"Qué tan seguro\" dice Media, confírmala antes de actuar."],
  ["Evidencia", "Cada fuga dice el archivo y la fila exacta que la prueba. Ábrelo en Excel y ve a esa fila: la fecha y el monto tienen que calzar."],
  ["Detalle", "Más abajo, cada fuga explicada con la fila original copiada, para que la reconozcas sin buscar."],
];

function pintarGuiaLectura(destino) {
  const d = crear("details", "guia-lectura");
  d.appendChild(crear("summary", "", "¿Cómo leo este informe? (1 minuto)"));
  const ol = crear("ol");
  for (const [t, texto] of GUIA_LECTURA) {
    const li = crear("li");
    li.append(crear("strong", "", t + ": "), document.createTextNode(texto));
    ol.appendChild(li);
  }
  d.appendChild(ol);
  destino.textContent = "";
  destino.appendChild(d);
}

function pintarMensajes(destino, borradores) {
  destino.textContent = "";
  const seccion = crear("section", "mensajes-cobro");
  seccion.appendChild(crear("h2", "", "Mensajes de cobro listos para enviar"));
  const mensajes = (borradores || []).filter((b) => b.clase === "mensaje");
  if (!mensajes.length) {
    seccion.appendChild(crear("p", "intro", "No hay cobros pendientes a clientes: no hace falta mandar mensajes."));
    destino.appendChild(seccion);
    return;
  }
  seccion.appendChild(crear("p", "intro", "Nada se ha enviado. Abre cada mensaje, haz lo que dice \"Antes de enviarlo\", cópialo con el botón, pégalo en tu correo o WhatsApp y completa lo que está entre corchetes."));
  for (const b of mensajes) {
    const d = crear("details", "mensaje");
    const s = crear("summary");
    s.append(crear("span", "codigo", b.codigo), crear("span", "para", b.para), crear("span", "monto", b.monto));
    d.appendChild(s);
    const antes = crear("p", "antes");
    antes.append(crear("strong", "", "Antes de enviarlo: "), document.createTextNode((b.antes || []).join(" ")));
    const asunto = crear("p", "asunto");
    asunto.append(crear("strong", "", "Asunto: "), document.createTextNode(b.asunto));
    const texto = crear("pre", "", b.cuerpo);
    const boton = crear("button", "boton secundario", "Copiar mensaje");
    boton.type = "button";
    boton.addEventListener("click", () => copiar("Asunto: " + b.asunto + "\n\n" + b.cuerpo, boton));
    d.append(antes, asunto, texto, boton);
    seccion.appendChild(d);
  }
  destino.appendChild(seccion);
}

async function copiar(texto, boton) {
  const original = boton.textContent;
  try {
    await navigator.clipboard.writeText(texto);
    boton.textContent = "Copiado: pégalo en tu correo";
  } catch (error) {
    boton.textContent = "No pude copiar: selecciona el texto a mano";
  }
  setTimeout(() => { boton.textContent = original; }, 2500);
}

/* Los codigos del plan (H01...) llevan al detalle de esa fuga dentro del informe de la misma vista. */
function enlazarPlan(plan, informe) {
  plan.addEventListener("click", (e) => {
    const a = e.target.closest("a.ir");
    if (!a) return;
    e.preventDefault();
    const destino = informe.querySelector('[id="' + a.dataset.id + '"]');
    if (!destino) return;
    destino.scrollIntoView({ behavior: "smooth", block: "start" });
    destino.classList.add("resaltado");
    setTimeout(() => destino.classList.remove("resaltado"), 2500);
  });
}

function pintarResultado(prefijo, datos) {
  pintarGuiaLectura($("guia-" + prefijo));
  $("plan-" + prefijo).innerHTML = datos.plan_html;
  pintarMensajes($("mensajes-" + prefijo), datos.borradores);
  $("informe-" + prefijo).innerHTML = datos.cuerpo_html;
}

/* ---------------------------------------------------------------- ejemplo precalculado */

async function mostrarDemo() {
  try {
    const [cuerpo, plan, borradores] = await Promise.all([
      traerTexto("demo/informe_cuerpo.html"), traerTexto("demo/plan_cuerpo.html"), traerTexto("demo/borradores.json")]);
    pintarResultado("demo", { cuerpo_html: cuerpo, plan_html: plan, borradores: JSON.parse(borradores) });
  } catch (error) {
    $("informe-demo").textContent = "No pude cargar el informe de ejemplo. Corre: python scripts/construir_web.py";
    return;
  }
  try {
    const p = JSON.parse(await traerTexto("demo/puntaje.json"));
    $("puntaje").textContent = "En esta empresa inventada el detective encontró " + p.encontradas + " de " + p.total +
      " fugas que escondimos a propósito" + (p.falsos === 0 ? " y no inventó ninguna." : " e inventó " + p.falsos + ".");
  } catch (error) { /* el puntaje es opcional */ }
  try {
    estado.manifiesto = JSON.parse(await traerTexto("py/manifiesto.json"));
    const span = $("archivos-demo");
    estado.manifiesto.demo.filter((n) => n !== "cotizaciones.csv").forEach((nombre, i, lista) => {
      const a = crear("a", "", nombre);
      a.href = "demo/datos/" + nombre;
      a.download = nombre;
      span.appendChild(a);
      if (i < lista.length - 1) span.appendChild(document.createTextNode(", "));
    });
  } catch (error) { /* la lista de archivos de ejemplo es opcional */ }
}

async function recalcularDemo() {
  const boton = $("recalcular");
  boton.disabled = true;
  try {
    const py = await motor("estado-demo");
    avisar("estado-demo", "Leyendo los archivos del ejemplo...");
    const archivos = new Map();
    for (const nombre of estado.manifiesto.demo) archivos.set(nombre, await traerBytes("demo/datos/" + nombre));
    escribirEntrada(py, archivos);
    avisar("estado-demo", "Buscando fugas...");
    const r = ejecutar(py, "auditar_entrada", "{}", "usted");
    if (r.error) throw new Error(r.error);
    pintarResultado("demo", r);
    avisar("estado-demo", "Listo: recalculado en tu navegador. " + r.hallazgos + " fugas, " + pesos(r.total_clp) +
      " en juego (el mismo resultado que el informe precalculado).");
  } catch (error) {
    avisar("estado-demo", error.message || String(error), true);
  } finally {
    boton.disabled = false;
  }
}

function pesos(n) {
  return "$" + String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/* ---------------------------------------------------------------- mis archivos */

async function reconocerTodo(py) {
  escribirEntrada(py, estado.archivos);
  avisar("estado-mios", "Reconociendo tus archivos...");
  estado.reconocidos = ejecutar(py, "reconocer");
  pintarTabla(estado.reconocidos);
  actualizarGuia();
}

async function agregarArchivos(lista) {
  const nuevos = Array.from(lista || []);
  if (!nuevos.length) return;
  try {
    for (const f of nuevos) estado.archivos.set(f.name, new Uint8Array(await f.arrayBuffer()));
    const py = await motor("estado-mios");
    await reconocerTodo(py);
    $("paso-revisar").hidden = false;
    $("resultado").hidden = true;
    etapa(2);
    const n = estado.reconocidos.filter((r) => r.rol).length;
    avisar("estado-mios", !estado.xlsx
      ? "Aviso: en este navegador no pude cargar el lector de Excel. Guarda tus planillas como CSV y vuelve a subirlas."
      : "Reconocí " + n + " de " + estado.reconocidos.length + (estado.reconocidos.length === 1 ? " archivo" : " archivos") +
        ". Mira abajo qué puedo revisar, y sigue en el paso 2.");
  } catch (error) {
    avisar("estado-mios", error.message || String(error), true);
  }
}

function pintarTabla(filas) {
  const cuerpo = $("tabla-archivos").querySelector("tbody");
  cuerpo.textContent = "";
  for (const f of filas) {
    const tr = crear("tr");
    const nombre = crear("td", "", f.nombre);
    const que = crear("td");
    if (f.rol === "config") {
      que.textContent = "Datos de tu empresa (nombre y último día que cubren tus archivos)";
    } else {
      const select = crear("select");
      select.dataset.archivo = f.nombre;
      select.dataset.detectado = f.rol;
      select.setAttribute("aria-label", "Qué es " + f.nombre);
      for (const r of estado.roles) select.appendChild(new Option(r.titulo, r.rol));
      select.appendChild(new Option("No usar este archivo", NO_USAR));
      select.value = f.rol || NO_USAR;
      select.addEventListener("change", actualizarGuia);
      que.appendChild(select);
      if (f.error) que.appendChild(crear("div", "problema", f.error));
    }
    const filasTd = crear("td", "", f.filas === null || f.filas === undefined ? "" : String(f.filas));
    const quitar = crear("td");
    const boton = crear("button", "boton secundario", "Quitar");
    boton.type = "button";
    boton.addEventListener("click", async () => {
      estado.archivos.delete(f.nombre);
      if (!estado.archivos.size) return limpiar();
      await reconocerTodo(await motor("estado-mios"));
    });
    quitar.appendChild(boton);
    tr.append(nombre, que, filasTd, quitar);
    cuerpo.appendChild(tr);
  }
  $("sin-config").hidden = tieneConfig();
}

function rolesElegidos() {
  const roles = {};
  for (const select of $("tabla-archivos").querySelectorAll("select")) {
    if (select.value !== select.dataset.detectado) roles[select.dataset.archivo] = select.value;
  }
  return roles;
}

function botonDescarga(nombre, etiqueta, ayuda, contenido, tipo) {
  const caja = crear("div", "descarga");
  const a = crear("a", "boton secundario", etiqueta);
  a.download = nombre;
  a.href = URL.createObjectURL(new Blob([contenido], { type: tipo + ";charset=utf-8" }));
  caja.append(a, crear("span", "nota", ayuda));
  return caja;
}

async function buscarFugas() {
  const boton = $("auditar");
  boton.disabled = true;
  try {
    if (!Object.keys(archivosPorRol()).length) throw new Error("No hay ningún archivo para revisar: sube al menos la cartola del banco.");
    const py = await motor("estado-mios");
    escribirEntrada(py, estado.archivos, configEscrita());
    avisar("estado-mios", "Buscando fugas y verificando cada fila...");
    const r = ejecutar(py, "auditar_entrada", JSON.stringify(rolesElegidos()), $("tratamiento").value);
    if (r.error) throw new Error(r.error);
    estado.ultimo = r;
    pintarResultado("mio", r);
    $("resumen-mio").textContent = r.hallazgos
      ? "Encontré " + r.hallazgos + (r.hallazgos === 1 ? " fuga" : " fugas") + " con " + pesos(r.total_clp) + " en juego."
      : "No encontré fugas con evidencia en tus archivos.";
    const descargas = $("descargas");
    descargas.textContent = "";
    descargas.append(
      botonDescarga("informe.html", "Informe para imprimir", "Para guardar, imprimir o mandárselo a tu contador. Se abre en cualquier navegador.", r.archivos["informe.html"], "text/html"),
      botonDescarga("mensajes_cobro.md", "Mensajes de cobro y notas", "Todos los mensajes y las notas internas en un archivo de texto.", r.archivos["mensajes_cobro.md"], "text/markdown"),
      botonDescarga("informe.md", "Informe en texto simple", "El mismo informe, en un archivo de texto liviano.", r.archivos["informe.md"], "text/markdown"),
      botonDescarga("hallazgos.json", "Datos para programas", "Solo si alguien te lo pide para procesarlo con otro programa.", r.archivos["hallazgos.json"], "application/json"));
    $("resultado").hidden = false;
    etapa(3);
    avisar("estado-mios", "Listo: " + r.hallazgos + (r.hallazgos === 1 ? " fuga" : " fugas") + ", " +
      pesos(r.total_clp) + " en juego. Tu informe está en el paso 3, más abajo.");
    $("resultado").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    avisar("estado-mios", error.message || String(error), true);
  } finally {
    boton.disabled = false;
  }
}

function limpiar() {
  estado.archivos.clear();
  estado.reconocidos = [];
  estado.ultimo = null;
  $("archivos").value = "";
  $("tabla-archivos").querySelector("tbody").textContent = "";
  $("paso-revisar").hidden = true;
  $("resultado").hidden = true;
  etapa(1);
  actualizarGuia();
  avisar("estado-mios", "");
}

function verModo(mios, desplazar) {
  $("vista-demo").hidden = mios;
  $("vista-mios").hidden = !mios;
  $("boton-demo").classList.toggle("activo", !mios);
  $("boton-mios").classList.toggle("activo", mios);
  $("boton-demo").setAttribute("aria-pressed", String(!mios));
  $("boton-mios").setAttribute("aria-pressed", String(mios));
  if (desplazar) $("boton-demo").scrollIntoView({ behavior: "smooth", block: "start" });
}

function iniciar() {
  pintarListaArchivos();
  actualizarGuia();
  enlazarPlan($("plan-demo"), $("informe-demo"));
  enlazarPlan($("plan-mio"), $("informe-mio"));
  $("boton-demo").addEventListener("click", () => verModo(false));
  $("boton-mios").addEventListener("click", () => verModo(true));
  $("empezar").addEventListener("click", () => verModo(true, true));
  $("ir-a-mios").addEventListener("click", () => verModo(true, true));
  $("ver-ejemplo").addEventListener("click", () => verModo(false, true));
  $("recalcular").addEventListener("click", recalcularDemo);
  $("auditar").addEventListener("click", buscarFugas);
  $("limpiar").addEventListener("click", limpiar);
  $("archivos").addEventListener("change", (e) => agregarArchivos(e.target.files));
  const zona = $("zona");
  for (const evento of ["dragenter", "dragover"]) {
    zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.add("encima"); });
  }
  for (const evento of ["dragleave", "drop"]) {
    zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.remove("encima"); });
  }
  zona.addEventListener("drop", (e) => agregarArchivos(e.dataTransfer.files));
  for (const evento of ["dragover", "drop"]) {
    window.addEventListener(evento, (e) => e.preventDefault());   // soltar fuera de la zona no abre el archivo
  }
  mostrarDemo();
}

document.addEventListener("DOMContentLoaded", iniciar);
