# 📨 Postulaciones Automatizadas con IA

Generá cartas de presentación personalizadas para cada oferta laboral usando Inteligencia Artificial.

**¿Qué hace?**
- Analizás la oferta de trabajo
- Cargás tu perfil una sola vez
- La IA genera una carta profesional adaptada a ese puesto específico
- También te da el resumen para poner en tu CV y las keywords que matcheás

---

## ✅ Requisitos previos

Antes de empezar necesitás tener instalado:

- **Python 3.10 o superior** → [Descargar acá](https://www.python.org/downloads/)
  - ⚠️ Durante la instalación marcá la opción **"Add Python to PATH"**
- **Git** → [Descargar acá](https://git-scm.com/downloads)

---

## 🚀 Instalación (una sola vez)

### Paso 1 — Descargar el proyecto

Abrí una terminal (CMD o PowerShell) y pegá esto:

```bash
git clone https://github.com/Ancarrizo/postulaciones-automatizadas.git
cd postulaciones-automatizadas
```

### Paso 2 — Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esperá que termine (puede tardar 1-2 minutos).

### Paso 3 — Configurar la API Key

1. Copiá el archivo `.env.example` y renombralo `.env`
2. Abrilo con el Bloc de notas
3. Reemplazá `sk-ant-...` con la API key que te pasó quien te compartió esto
4. Guardá el archivo

El archivo tiene que quedar así:
```
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXX
```

### Paso 4 — Iniciar la aplicación

```bash
python web/app.py
```

Se abre el navegador automáticamente en `http://localhost:5000`

---

## 📋 Cómo usarlo

### Primera vez: cargá tu perfil

1. Hacé clic en **"Mi Perfil"**
2. Completá tus datos: nombre, email, educación, experiencia, etc.
3. Subí tu CV (PDF o DOCX)
4. Clic en **"Guardar perfil"**

> 💡 Cuanta más información pongas en el perfil, mejor va a quedar la carta.

### Generar una carta

1. Hacé clic en **"✍️ Generar carta"**
2. Completá:
   - **Empresa**: nombre de la empresa
   - **Puesto**: el rol al que te postulás
   - **Descripción**: pegá el texto de la oferta (opcional pero recomendado)
3. Clic en **"✨ Generar carta"**
4. En segundos vas a ver:
   - 🎯 **Keywords** que matcheás con la oferta
   - 📄 **Resumen** para poner al principio de tu CV
   - ✉️ **Carta** lista para copiar y pegar

---

## ❓ Preguntas frecuentes

**¿Mis datos se guardan en algún servidor?**
No. Todo corre en tu computadora. El perfil se guarda en tu navegador (sesión local).

**¿La carta suena robótica?**
No, Claude genera texto natural en español rioplatense, adaptado específicamente al puesto. Podés editarla antes de enviarla.

**¿Puedo generar varias cartas?**
Sí, las que quieras. Cada una se adapta a la oferta que ingresás.

**¿Qué pongo en "Descripción de la oferta"?**
Copiá y pegá el texto completo de la oferta de trabajo (de LinkedIn, Computrabajo, etc.). Cuanto más detalle, mejor la carta.

**La app no abre / hay un error**
Probá cerrar y volver a correr `python web/app.py`. Si el error persiste, mandá captura de pantalla.

---

## 🛠️ Problemas comunes

| Error | Solución |
|---|---|
| `python: command not found` | Reinstalá Python y marcá "Add to PATH" |
| `pip: command not found` | Usá `python -m pip install -r requirements.txt` |
| `ModuleNotFoundError` | Volvé a correr `pip install -r requirements.txt` |
| La página no abre | Escribí manualmente `http://localhost:5000` en el navegador |

---

## 📬 Contacto

Proyecto creado por **Andrés Carrizo** — La Plata, Buenos Aires.

[linkedin.com/in/andressalvadorcarrizo](https://linkedin.com/in/andressalvadorcarrizo)
