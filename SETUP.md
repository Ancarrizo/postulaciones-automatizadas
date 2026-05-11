# Setup — Postulaciones Andrés Carrizo

## Paso 1 — API Key de Anthropic
1. Entrá a https://console.anthropic.com/settings/keys
2. Creá una key nueva
3. Copiá el archivo `.env.example` como `.env` y pegá tu key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Paso 2 — Credenciales de Gmail (una sola vez)

### 2a. Crear proyecto en Google Cloud
1. Ir a https://console.cloud.google.com
2. Crear un proyecto nuevo (ej: "Postulaciones")
3. Menú → **APIs y servicios** → **Biblioteca**
4. Buscar **Gmail API** → Habilitar

### 2b. Crear credenciales OAuth2
1. Menú → **APIs y servicios** → **Credenciales**
2. Clic en **+ Crear credenciales** → **ID de cliente de OAuth**
3. Tipo: **Aplicación de escritorio**
4. Nombre: cualquiera (ej: "postulaciones-script")
5. Descargar el JSON → renombrarlo `credentials.json`
6. Moverlo a la carpeta `/postulaciones/`

### 2c. Agregar tu cuenta como usuario de prueba
1. Menú → **APIs y servicios** → **Pantalla de consentimiento de OAuth**
2. Scroll hasta **Usuarios de prueba** → Agregar `Andicarrizo5@gmail.com`

## Paso 3 — Agregar los CVs
Copiar los archivos en la carpeta `cvs/`:
- `cvs/CV_Andres_Carrizo_Salud.docx`
- `cvs/CV_Andres_Carrizo_2026.docx`

## Paso 4 — Correr el script

### Ver cartas sin tocar Gmail (recomendado primero)
```bash
cd postulaciones
python main.py --dry-run
```

### Crear borradores reales en Gmail
```bash
python main.py
```
La primera vez abre el navegador para que autorices. Después queda guardado.

Luego abrís **Gmail → Borradores**, revisás cada uno y enviás.
