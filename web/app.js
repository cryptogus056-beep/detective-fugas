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
const estado = { motor: null, roles: [], archivos: new Map(), xlsx: false, manifiesto: null, ultimo: null };

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

/* ---------------------------------------------------------------- demo precalculada */

async function mostrarDemo() {
  try {
    $("informe-demo").innerHTML = await traerTexto("demo/informe_cuerpo.html");
  } catch (error) {
    $("informe-demo").textContent = "No pude cargar el informe de la demo. Corre: python scripts/construir_web.py";
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
    estado.manifiesto.demo.forEach((nombre, i) => {
      const a = document.createElement("a");
      a.href = "demo/datos/" + nombre;
      a.download = nombre;
      a.textContent = nombre;
      span.appendChild(a);
      if (i < estado.manifiesto.demo.length - 1) span.appendChild(document.createTextNode(", "));
    });
  } catch (error) { /* la lista de archivos de ejemplo es opcional */ }
}

async function recalcularDemo() {
  const boton = $("recalcular");
  boton.disabled = true;
  try {
    const py = await motor("estado-demo");
    avisar("estado-demo", "Leyendo los archivos de la demo...");
    const archivos = new Map();
    for (const nombre of estado.manifiesto.demo) archivos.set(nombre, await traerBytes("demo/datos/" + nombre));
    escribirEntrada(py, archivos);
    avisar("estado-demo", "Buscando fugas...");
    const r = ejecutar(py, "auditar_entrada", "{}", "usted");
    if (r.error) throw new Error(r.error);
    $("informe-demo").innerHTML = r.cuerpo_html;
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

async function agregarArchivos(lista) {
  const nuevos = Array.from(lista || []);
  if (!nuevos.length) return;
  try {
    for (const f of nuevos) estado.archivos.set(f.name, new Uint8Array(await f.arrayBuffer()));
    const py = await motor("estado-mios");
    escribirEntrada(py, estado.archivos);
    avisar("estado-mios", "Reconociendo tus archivos...");
    pintarTabla(ejecutar(py, "reconocer"));
    $("paso-revisar").hidden = false;
    $("resultado").hidden = true;
    avisar("estado-mios", estado.xlsx ? "" :
      "Aviso: en este navegador no pude cargar el lector de Excel. Guarda tus planillas como CSV y vuelve a subirlas.");
  } catch (error) {
    avisar("estado-mios", error.message || String(error), true);
  }
}

function pintarTabla(filas) {
  const cuerpo = $("tabla-archivos").querySelector("tbody");
  cuerpo.textContent = "";
  for (const f of filas) {
    const tr = document.createElement("tr");
    const nombre = document.createElement("td");
    nombre.textContent = f.nombre;
    const que = document.createElement("td");
    if (f.rol === "config") {
      que.textContent = "Datos de tu empresa (nombre y último día que cubren tus archivos)";
    } else {
      const select = document.createElement("select");
      select.dataset.archivo = f.nombre;
      select.dataset.detectado = f.rol;
      select.setAttribute("aria-label", "Qué es " + f.nombre);
      for (const r of estado.roles) select.appendChild(new Option(r.titulo, r.rol));
      select.appendChild(new Option("No usar este archivo", NO_USAR));
      select.value = f.rol || NO_USAR;
      que.appendChild(select);
      if (f.error) {
        const p = document.createElement("div");
        p.className = "problema";
        p.textContent = f.error;
        que.appendChild(p);
      }
    }
    const filasTd = document.createElement("td");
    filasTd.textContent = f.filas === null || f.filas === undefined ? "" : String(f.filas);
    const quitar = document.createElement("td");
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "boton secundario";
    boton.textContent = "Quitar";
    boton.addEventListener("click", async () => {
      estado.archivos.delete(f.nombre);
      if (!estado.archivos.size) return limpiar();
      const py = await motor("estado-mios");
      escribirEntrada(py, estado.archivos);
      pintarTabla(ejecutar(py, "reconocer"));
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

function botonDescarga(nombre, contenido, tipo) {
  const a = document.createElement("a");
  a.className = "boton secundario";
  a.textContent = "Descargar " + nombre;
  a.download = nombre;
  a.href = URL.createObjectURL(new Blob([contenido], { type: tipo + ";charset=utf-8" }));
  return a;
}

async function buscarFugas() {
  const boton = $("auditar");
  boton.disabled = true;
  try {
    const py = await motor("estado-mios");
    escribirEntrada(py, estado.archivos, configEscrita());
    avisar("estado-mios", "Buscando fugas y verificando cada fila...");
    const r = ejecutar(py, "auditar_entrada", JSON.stringify(rolesElegidos()), $("tratamiento").value);
    if (r.error) throw new Error(r.error);
    estado.ultimo = r;
    $("informe-mio").innerHTML = r.cuerpo_html;
    $("texto-mensajes").textContent = r.archivos["mensajes_cobro.md"];
    const descargas = $("descargas");
    descargas.textContent = "";
    descargas.append(
      botonDescarga("informe.md", r.archivos["informe.md"], "text/markdown"),
      botonDescarga("hallazgos.json", r.archivos["hallazgos.json"], "application/json"),
      botonDescarga("mensajes_cobro.md", r.archivos["mensajes_cobro.md"], "text/markdown"),
      botonDescarga("informe.html", r.archivos["informe.html"], "text/html"));
    $("resultado").hidden = false;
    avisar("estado-mios", "Listo: " + r.hallazgos + (r.hallazgos === 1 ? " fuga" : " fugas") + ", " +
      pesos(r.total_clp) + " en juego. El informe está más abajo.");
    $("resultado").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    avisar("estado-mios", error.message || String(error), true);
  } finally {
    boton.disabled = false;
  }
}

function limpiar() {
  estado.archivos.clear();
  estado.ultimo = null;
  $("archivos").value = "";
  $("tabla-archivos").querySelector("tbody").textContent = "";
  $("paso-revisar").hidden = true;
  $("resultado").hidden = true;
  avisar("estado-mios", "");
}

function verModo(mios) {
  $("vista-demo").hidden = mios;
  $("vista-mios").hidden = !mios;
  $("boton-demo").classList.toggle("activo", !mios);
  $("boton-mios").classList.toggle("activo", mios);
  $("boton-demo").setAttribute("aria-pressed", String(!mios));
  $("boton-mios").setAttribute("aria-pressed", String(mios));
}

function iniciar() {
  $("boton-demo").addEventListener("click", () => verModo(false));
  $("boton-mios").addEventListener("click", () => verModo(true));
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
