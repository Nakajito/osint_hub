Diagnóstico: FaceVerify — App ciclada en PENDING

  Arquitectura identificada

  [Web Container]  ──Redis──  [Celery Worker Container]
     /tmp/faceverify_*             /app/media (shared vol)
     /app/media (shared vol)       /home/appuser/.deepface (vol)

  ---
  CAUSAS RAÍZ (confirmadas con evidencia)

  ---
  🔴 CAUSA 1 — CRÍTICA: Aislamiento de filesystem entre contenedores

  Evidencia directa:
  Web container:  /tmp/faceverify_w12apv61/a_mara3.jpg  ✅ EXISTE
  Worker:         /tmp/faceverify_w12apv61/              ❌ INVISIBLE

  El flujo roto:
  1. views.py usa tempfile.mkdtemp() → crea /tmp/faceverify_XXXX/ en el contenedor web
  2. Guarda las imágenes allí y pasa las rutas al task de Celery
  3. El worker (contenedor separado) recibe esas rutas — pero no comparte /tmp con el web
  4. DeepFace.verify(img1_path, img2_path, ...) lanza FileNotFoundError
  5. except Exception as e lo captura → devuelve {"ok": False, "error": "...FileNotFoundError..."}
  6. La tarea termina como SUCCESS con ok=False → el frontend llama a showError() y muestra el error

  El único volumen compartido entre ambos contenedores es /app/media — las imágenes nunca llegan al worker.

  # views.py:31 — EL PROBLEMA
  tmp_dir = tempfile.mkdtemp(prefix="faceverify_")  # ← /tmp/ del contenedor web, INVISIBLE al worker

  ---
  🔴 CAUSA 2 — CRÍTICA: Modelo ArcFace nunca se descarga (volume mal configurado)

  Evidencia:
  HOME=/app                                     ← env en el contenedor
  DeepFace busca pesos en: $HOME/.deepface  =  /app/.deepface/weights/  (VACÍO)
  Volume montado en:                           /home/appuser/.deepface   (NUNCA SE USA)

  El Dockerfile declara useradd -r -g appuser -d /app appuser → HOME=/app. Pero el docker-compose.yaml monta el volume en /home/appuser/.deepface. Son paths
   distintos.

  Consecuencia: Cada reinicio del contenedor, los pesos del modelo ArcFace (~400 MB) se pierden. Al ejecutar la primera tarea, DeepFace intenta descargar el
   modelo desde Google Drive. Este proceso puede tardar 10-30 minutos dependiendo del ancho de banda.

  El frontend tiene un timeout de 180 segundos (120 polls × 1.5s). El usuario ve el loader girar durante 3 minutos y luego obtiene "Tiempo de espera
  agotado" — esto es el comportamiento "ciclado" reportado.

  ---
  🟡 CAUSA 3 — MODERADA: El resultado expira antes de que el usuario lo vea (si la tarea eventualmente completa)

  # settings.py
  CELERY_RESULT_EXPIRES = 3600  # 1 hora en Redis

  La tarea que se muestra en los logs (1bd32a81-8175-4430-a145-e98425578709) fue sometida hace +5 horas — su resultado ya expiró de Redis. Por eso el estado
   muestra PENDING ahora: no hay entrada en el backend de resultados.

  Redis → 0 task results    ← confirmado
  Redis → 0 tasks in queue  ← confirmado

  ---
  🟡 CAUSA 4 — MENOR: Worker arranca sin esperar a que Redis esté listo

  [2026-05-02 20:08:02] ERROR: Cannot connect to redis://...Connection refused.
  [2026-05-02 20:08:04] ERROR: Cannot connect...Connection refused.
  [2026-05-02 20:08:08] ERROR: Cannot connect...Temporary failure in name resolution.

  No hay depends_on con healthcheck para Redis en el docker-compose.yaml. El worker arranca antes que Redis esté disponible y entra en retry loop. Se
  recupera solo, pero puede perder tareas enviadas en esa ventana.

  ---
  PLAN DE SOLUCIONES

  Fix 1 — INMEDIATO (requiere redeploy del código)

  Cambiar views.py para usar el volumen compartido /app/media:

  # FaceVerify/views.py — línea 31
  # ❌ ANTES:
  tmp_dir = tempfile.mkdtemp(prefix="faceverify_")

  # ✅ DESPUÉS:
  import uuid
  from django.conf import settings

  tmp_dir = os.path.join(settings.MEDIA_ROOT, "tmp", f"faceverify_{uuid.uuid4().hex}")
  os.makedirs(tmp_dir, exist_ok=True)

  Ambos contenedores montan /app/media → el worker podrá leer las imágenes.

  ---
  Fix 2 — CRÍTICO (fix al docker-compose.yaml en Coolify)

  Opción A — Corregir el path del volume (más limpio):

  En el docker-compose.yaml, cambiar el volume del worker:
  celery-worker-osint:
    volumes:
      - 'yq9bqioxwdg7bjsdcvnrrn88-osint-volume:/app/media'
      - 'osint-deepface-weights:/app/.deepface'   # ← antes era /home/appuser/.deepface

  Opción B — Alternativa: añadir variable de entorno HOME:

  En el env del worker en Coolify agregar: HOME=/home/appuser y verificar que el directorio exista en el Dockerfile.

  ---
  Fix 3 — RECOMENDADO: Pre-descargar ArcFace en el Dockerfile (bake en imagen)

  Agregar al Dockerfile (stage runtime, antes de USER appuser):
  # Pre-descarga el modelo ArcFace para evitar descarga en runtime
  RUN python -c "
  import os; os.environ['HOME'] = '/app'
  from deepface.modules import modeling
  modeling.build_model('ArcFace')
  " 2>/dev/null || true

  Esto embebe el modelo (~400MB) en la imagen Docker. Elimina cualquier latencia de descarga en producción.

  ---
  Fix 4 — MENOR: Agregar healthcheck Redis en docker-compose

  celery-worker-osint:
    depends_on:
      yemkdfkxbzd3a4n37i2bca0w:
        condition: service_healthy

  ---
  Fix 5 — MENOR: Aumentar TTL de resultados o usar DB backend

  # settings.py
  CELERY_RESULT_EXPIRES = 86400  # 24 horas en lugar de 1 hora

  # O usar django_celery_results con DB (ya está instalado):
  CELERY_RESULT_BACKEND = 'django-db'

  ---
  Orden de implementación recomendado

  ┌───────────┬────────────────────────────────────────────┬────────────────────────────────────┬──────────┐
  │ Prioridad │                    Fix                     │              Impacto               │ Esfuerzo │
  ├───────────┼────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ 1         │ Fix views.py — usar /app/media/tmp/        │ Desbloquea la funcionalidad        │ Bajo     │
  ├───────────┼────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ 2         │ Corregir volume deepface en docker-compose │ Persiste el modelo entre reinicios │ Muy bajo │
  ├───────────┼────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ 3         │ Pre-descargar ArcFace en Dockerfile        │ Elimina latencia inicial           │ Medio    │
  ├───────────┼────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ 4         │ depends_on Redis healthcheck               │ Estabilidad de arranque            │ Bajo     │
  ├───────────┼────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ 5         │ Aumentar CELERY_RESULT_EXPIRES             │ UX de resultados                   │ Muy bajo │
  └───────────┴────────────────────────────────────────────┴────────────────────────────────────┴──────────┘

  Los fixes 1 y 2 son los únicos necesarios para que FaceVerify funcione. El fix 1 es el bloqueador principal: sin él, el worker nunca puede acceder a las
  imágenes subidas.