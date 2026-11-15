# Paso a paso para Gustavo: Detective de Fugas con Fable 5.2

Esta guía parte desde cero. Sigue los pasos en orden. Lo marcado **[sin verificar]** no lo pude comprobar en la fuente oficial: revísalo en pantalla.

Fecha límite del concurso: **jueves 19 de noviembre, 23:59 (hora de Chile)**. Meta: publicar **antes de las 20:00** del jueves, con margen.

---

## Calendario sugerido

| Día | Qué haces tú | Qué hace Fable |
|---|---|---|
| **Sáb 14** (hoy, 30 min) | Pasos 1 a 6: preparar, abrir Claude Code, pegar P0 y aprobar el plan con P1 | Lee todo, arma el plan y empieza a construir |
| **Dom 15** | Revisar cada tanto; si se corta, retomar con P2 | Motor de detección, demo A y demo B (fases 1 a 4) |
| **Lun 16** | Igual que el domingo. Meta: terminar todo lo pesado hoy | Modo agéntico, web y crítico (fases 5 a 7) |
| **Mar 17** | Crítico si falta (P5 y P6), verificación final (P7), README (P8), subir a GitHub y Vercel (pasos 10 y 11) | Correcciones y documentación |
| **Mié 18** | Guion (P9) y grabar el video (paso 12) | Actualiza el guion con números reales |
| **Jue 19** | Borradores finales (P10), publicar en X y luego en Skool **antes de las 20:00** (paso 13) | Nada: tú publicas |

¿Por qué cargar el trabajo pesado antes del lunes 16? Porque podría ser el último día en que Fable 5.2 viene incluido en el plan Pro **[sin verificar]**. Revisa en claude.ai la fecha real.

---

## Paso 1 · Lo que necesitas instalado

- **Python 3.10 o más nuevo.** Revisa con `python3 --version` (en Windows: `py --version`).
- **Git.** Revisa con `git --version`.
- **Claude Code v2.1.321 o más nuevo** (Fable 5.2 lo exige, según la documentación oficial de Claude Code). Actualiza con:
  ```bash
  claude update
  ```
- **Node.js** (solo si vas a desplegar en Vercel desde la terminal; si lo haces desde la web de Vercel, no hace falta).

## Paso 2 · Copia la carpeta

1. Descarga `detective-fugas.zip` y descomprímelo donde guardas tus proyectos (por ejemplo `Documentos/proyectos/`).
2. Abre una terminal dentro de la carpeta:
   ```bash
   cd ~/Documentos/proyectos/detective-fugas
   ```

## Paso 3 · Prepara Python y comprueba el dataset

```bash
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generar_dataset.py --todas
```

Debe decir: `Variante A: 12 fugas escondidas en data/demo` y lo mismo para la B. Si lo ves, el dataset está bien.

## Paso 4 · Inicia Git (solo local, todavía no se sube nada)

```bash
git init
git add .
git commit -m "kit inicial: spec, dataset ficticio y evaluador"
```

## Paso 5 · Abre Claude Code con Fable 5.2 y esfuerzo alto

Dentro de la carpeta:

```bash
claude --model fable --effort high
```

O, si ya tienes Claude Code abierto, escribe estos dos comandos:

```
/model fable
/effort high
```

Comprueba con `/status` que diga Fable 5.2. Estos comandos salen en la documentación oficial de Claude Code (code.claude.com/docs/en/model-config). Al confirmar con `/effort high` y Enter, queda guardado como tu nivel por defecto para Fable.

## Paso 6 · Arranca a Fable

1. Abre `PROMPTS.md`, copia **P0** completo y pégalo en Claude Code.
2. Fable va a leer todo y escribir `PLAN.md`. Te va a mostrar un resumen de 10 líneas.
3. Léelo. Si te parece bien, copia y pega **P1** ("Sí, aprobado el PLAN.md..."). Desde ahí trabaja solo.

### Qué aprobar cuando Claude Code te pida permiso

Claude Code te pregunta antes de editar archivos o correr comandos.

- **Aprueba** (puedes elegir la opción de no volver a preguntar para ese comando **[sin verificar el texto exacto del botón]**): crear y editar archivos dentro de `detective-fugas`, `python`, `pytest`, `pip install`, `git add`, `git commit`, `git status`, `git log`, `python -m http.server`.
- **Rechaza siempre:** `git push`, `vercel`, `npx vercel`, cualquier cosa que borre fuera de la carpeta, comandos que envíen datos a internet (`curl` o `wget` a sitios raros) y todo lo que mencione tus claves.
- La carpeta `.claude/settings.json` ya bloquea `git push`, `vercel` y la lectura de la llave de respuestas, como segunda capa de seguridad.

## Paso 7 · Si se corta por el límite del plan Pro

El plan Pro tiene un límite de uso que se reinicia cada cierto tiempo (suele ser una ventana de unas 5 horas **[sin verificar]**). Claude Code te avisa cuándo se reinicia.

1. Espera a la hora que te indica.
2. Vuelve a la carpeta y continúa la última conversación:
   ```bash
   claude --continue
   ```
   (o `claude --resume` para elegir de una lista).
3. Revisa con `/status` que sigas en Fable con esfuerzo alto.
4. Pega **P2**. Fable lee `PLAN.md` y la bitácora y sigue donde quedó.

Si en algún momento Fable se detiene y te pregunta "¿continúo?", pega **P3**. Si quieres saber cómo va sin interrumpir, usa **P4**.

## Paso 8 · Cómo revisar el resultado tú mismo

En una terminal aparte (con el `.venv` activado):

```bash
python scripts/evaluar.py --dataset data/demo
python scripts/evaluar.py --dataset data/demo_b
python -m pytest -q
```

- Buscas **"RESULTADO: APROBADO"** en las dos demos: significa al menos 10 de 12 fugas y 0 inventadas.
- El informe está en `salida/demo/informe.md`. Ábrelo y elige un hallazgo: abre el archivo que cita (por ejemplo `data/demo/cartola_banco.csv` en Excel) y ve a la fila que dice. Debe calzar la fecha y el monto.

Para ver la web en tu computador:

```bash
python scripts/construir_web.py
python -m http.server -d web 8000
```

Abre `http://localhost:8000` en el navegador. Para cerrar el servidor, `Ctrl + C`.

## Paso 9 · El crítico (lunes o martes)

1. En Claude Code escribe `/clear` (o abre una sesión nueva) para que el crítico no sepa nada del proyecto.
2. Pega **P5**. El crítico deja hasta 5 problemas en `CRITICO.md`.
3. Vuelve a la sesión principal (`claude --continue` o `claude --resume`) y pega **P6** para que Fable los corrija.
4. Después pega **P7** (verificación final) y **P8** (README).

Si Fable ya hizo el crítico solo dentro de la fase 7 (la spec se lo pide), puedes saltarte P5 y P6.

## Paso 10 · Subir a GitHub (lo haces tú)

1. Pega **P11** en Claude Code. Fable revisa que no haya nada sensible y te da los comandos.
2. En github.com, crea un repositorio nuevo **público** llamado `detective-fugas`, sin README (ya tienes uno).
3. En la terminal:
   ```bash
   git remote add origin https://github.com/TU_USUARIO/detective-fugas.git
   git branch -M main
   git push -u origin main
   ```
   Si tienes la herramienta `gh` instalada, también sirve: `gh repo create detective-fugas --public --source=. --push`.

## Paso 11 · Publicar la web en Vercel (lo haces tú)

**Opción A, desde la web de Vercel (la más fácil):**

1. Entra a vercel.com con tu cuenta de GitHub.
2. "Add New..." → "Project" → importa `detective-fugas` **[sin verificar los nombres exactos de los botones]**.
3. En **Root Directory** elige `web`. En el tipo de proyecto (Framework Preset) elige "Other". Sin comando de build.
4. Deploy. Copia el link que te da (algo como `detective-fugas.vercel.app`).

Importante: como la web usa una copia del código, corre `python scripts/construir_web.py` y haz commit y push ANTES de desplegar, para que `web/` tenga la última versión.

**Opción B, desde la terminal:**

```bash
cd web
npx vercel --prod
```

Abre el link en tu celular y comprueba que la demo carga.

## Paso 12 · Grabar el video (miércoles)

1. Pega **P9** para que Fable actualice `ENTREGA/guion_video.md` con los números reales.
2. Graba la pantalla con tu voz, siguiendo el guion (2 a 3 minutos):
   - Mac: `Cmd + Shift + 5`.
   - Windows: `Win + Alt + R` (Xbox Game Bar) o la herramienta Recortes **[sin verificar en tu versión de Windows]**.
   - También sirven OBS o Loom.
3. Súbelo a YouTube como "No listado" (o a Loom) y copia el link.

## Paso 13 · Publicar (jueves 19, antes de las 20:00)

1. Pega **P10**: Fable deja los borradores finales con los números reales.
2. Completa los marcadores `[[LINK_WEB]]`, `[[LINK_VIDEO]]` y `[[LINK_GITHUB]]`.
3. **Primero X:** publica `ENTREGA/post_x.md` (opción A) con #FableImperial. Copia el link del post.
4. **Después Skool:** crea el post con el título exacto `[FABLE] Detective de Fugas: encuentra la plata que tu pyme pierde sin darse cuenta`, pega el contenido de `ENTREGA/post_skool.md` y reemplaza `[[LINK_POST_X]]` por el link del paso anterior.
5. Revisa que se vean las 4 partes: el proyecto, el resultado (link y video), cómo lo hiciste y la moraleja.

Recuerda: puedes mandar hasta 2 entradas. Esta es una.

---

## Si algo sale mal

| Problema | Qué hacer |
|---|---|
| `claude: command not found` | Reinstala Claude Code siguiendo la documentación oficial y abre una terminal nueva |
| "Model not supported" al elegir Fable | `claude update` y vuelve a intentar |
| `ModuleNotFoundError: openpyxl` | Activa el `.venv` (paso 3) y corre `pip install -r requirements.txt` |
| `evaluar.py` dice "NO APROBADO" | Pega P2 o P3: Fable ve el detalle y corrige |
| La web se ve en blanco | Abre la consola del navegador (F12), copia el error y pégaselo a Fable |
| Fable pide permiso para `git push` | Recházalo. Tú lo haces en el paso 10 |
