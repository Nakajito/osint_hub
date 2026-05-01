# Lessons Learned

## FaceVerify — DeepFace + Celery + polling AJAX (2026-05-01)

### Deferred TF import evita carga en proceso web
`from deepface import DeepFace` dentro del cuerpo de la task Celery, no en el nivel de módulo. TensorFlow tarda ~5s en cargar; hacerlo al arrancar el worker web congela las peticiones. Import diferido carga TF solo en el proceso worker.

### tests con ImageField necesitan PIL-valid bytes
`forms.ImageField` llama `PIL.Image.open()` en validación. Tests con `b"\x00" * n` fallan con "Seleccione una imagen válida". Solución: usar `io.BytesIO` + `Image.new(...).save(buf, format="PNG")` para generar PNG real mínimo. Override `f.size` para tests de tamaño máximo (PIL valida contenido, no size).

### sys.modules patching para imports diferidos en tasks
`from deepface import DeepFace` dentro de una función → `patch.dict("sys.modules", {"deepface": mock_module})` antes de importar el módulo. El mock resuelve `from deepface import DeepFace` como `mock_module.DeepFace` (atributo). Configurar `mock_module.DeepFace.verify.return_value` o `.side_effect`.

### pytest.ini: testpaths restringe descubrimiento
Si apps Django tienen `tests.py` fuera del directorio `tests/`, actualizar `pytest.ini`:
```ini
python_files = test_*.py tests.py
testpaths = tests NombreApp
```

### Volumen Docker para pesos DeepFace
ArcFace descarga ~130 MB en `~/.deepface/weights/` al primer uso. Sin volumen persistente, cada deploy redescarga. Montar mismo volumen en `web` y `celery_worker` para compartir cache.

### Polling AJAX: interceptar form submit con fetch
Patrón para long-running tasks en Django sin htmx:
1. POST form via `fetch()` → retorna 202 + `task_id`
2. `setInterval(1500ms)` → GET `/status/<id>/` → JSON `{state, result}`
3. En `SUCCESS`/`FAILURE`: `clearInterval`, ocultar loader, mostrar resultado

CSRF: leer cookie `csrftoken`, pasar en header `X-CSRFToken`.

### mypy: UploadedFile.size es Optional[int]
`f.size > MAX_SIZE` falla mypy. Usar `(f.size or 0) > MAX_SIZE`. Similar con `uploaded.name` (puede ser `None`): `uploaded.name or "img"`.

### ruff no estaba en pyproject.toml
Proyecto usa `black==25.12.0` ya instalado pero `ruff` faltaba. Añadir:
```
uv add --dev ruff mypy django-stubs
```
