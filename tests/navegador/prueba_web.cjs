/* Prueba la web en un navegador real (Playwright + Chromium).
 *
 *   node tests/navegador/prueba_web.cjs <url> <carpeta con archivos para subir> [carpeta para capturas]
 *
 * Imprime un JSON con lo que vio: textos, errores de consola, dominios contactados,
 * metodos HTTP usados y el hallazgos.json que calculo el navegador.
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [url, carpeta, capturas] = process.argv.slice(2);
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage({ viewport: { width: 1200, height: 900 } });
  const visto = { errores: [], dominios: new Set(), metodos: new Set(), fallidas: [] };
  pagina.on("console", (m) => { if (m.type() === "error") visto.errores.push(m.text()); });
  pagina.on("pageerror", (e) => visto.errores.push(String(e)));
  pagina.on("request", (r) => { visto.dominios.add(new URL(r.url()).hostname); visto.metodos.add(r.method()); });
  pagina.on("requestfailed", (r) => visto.fallidas.push(r.url()));

  const salida = {};
  await pagina.goto(url, { waitUntil: "load" });
  await pagina.waitForSelector("#informe-demo .informe h1", { timeout: 20000 });
  await pagina.waitForFunction(() => document.getElementById("puntaje").textContent.length > 0, null, { timeout: 10000 });
  salida.titulo = await pagina.textContent("header h1");
  salida.cabecera = await pagina.textContent("header");
  salida.aviso_demo = await pagina.textContent("#vista-demo .aviso");
  salida.fugas_demo = await pagina.locator("#informe-demo .fuga").count();
  salida.titulo_informe = await pagina.textContent("#informe-demo .informe h1");
  salida.dominios_solo_demo = [...visto.dominios];
  if (capturas) await pagina.screenshot({ path: path.join(capturas, "demo_escritorio.png"), fullPage: false });

  // Subir archivos propios
  await pagina.click("#boton-mios");
  const archivos = fs.readdirSync(carpeta).filter((n) => fs.statSync(path.join(carpeta, n)).isFile() && /\.(csv|xlsx|json)$/i.test(n))
    .map((n) => path.join(carpeta, n));
  await pagina.setInputFiles("#archivos", archivos);
  await pagina.waitForFunction((n) => document.querySelectorAll("#tabla-archivos tbody tr").length === n, archivos.length, { timeout: 180000 });
  salida.roles = await pagina.$$eval("#tabla-archivos tbody tr", (filas) => filas.map((tr) => {
    const select = tr.querySelector("select");
    return [tr.children[0].textContent, select ? select.value : "config", tr.children[2].textContent];
  }));
  if (capturas) await pagina.screenshot({ path: path.join(capturas, "mios_revisar.png"), fullPage: true });
  await pagina.click("#auditar");
  await pagina.waitForSelector("#resultado:not([hidden]) .informe h1", { timeout: 120000 });
  salida.estado_mios = await pagina.textContent("#estado-mios");
  salida.hallazgos_json = await pagina.evaluate(() => estado.ultimo.archivos["hallazgos.json"]);
  salida.informe_md = await pagina.evaluate(() => estado.ultimo.archivos["informe.md"]);
  salida.mensajes_md = await pagina.evaluate(() => estado.ultimo.archivos["mensajes_cobro.md"]);
  salida.descargas = await pagina.$$eval("#descargas a", (as) => as.map((a) => a.download));
  salida.xlsx = await pagina.evaluate(() => estado.xlsx);
  if (capturas) await pagina.screenshot({ path: path.join(capturas, "mios_resultado.png"), fullPage: false });

  // Volver a calcular la demo en el navegador (usa el XLSX de la demo)
  await pagina.click("#boton-demo");
  await pagina.click("#recalcular");
  await pagina.waitForFunction(() => /^Listo|^No pude|Error/i.test(document.getElementById("estado-demo").textContent)
    || document.getElementById("estado-demo").classList.contains("error"), null, { timeout: 120000 });
  salida.estado_demo = await pagina.textContent("#estado-demo");
  salida.fugas_demo_recalculada = await pagina.locator("#informe-demo .fuga").count();

  if (capturas) {
    await pagina.setViewportSize({ width: 390, height: 844 });
    await pagina.screenshot({ path: path.join(capturas, "demo_celular.png"), fullPage: false });
    await pagina.evaluate(() => document.querySelector("#informe-demo table").scrollIntoView());
    await pagina.screenshot({ path: path.join(capturas, "demo_celular_tabla.png"), fullPage: false });
    salida.ancho_celular = await pagina.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  }
  salida.errores = visto.errores;
  salida.dominios = [...visto.dominios].sort();
  salida.metodos = [...visto.metodos].sort();
  salida.fallidas = visto.fallidas;
  await navegador.close();
  console.log(JSON.stringify(salida));
})().catch((error) => { console.error(String(error && error.stack || error)); process.exit(1); });
