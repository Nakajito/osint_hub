import logging
import trio
import httpx
import importlib
import pkgutil
from celery import shared_task
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def search_phone_task(self, phone, country_code):
    """
    Celery task para búsqueda de teléfonos.
    """
    try:
        logger.info(f"Iniciando búsqueda para teléfono: {phone}, país: {country_code}")

        # Ejecutar async function sincrónicamente
        results = async_to_sync(search_phone_async)(phone, country_code)

        logger.info(f"Búsqueda completada. Resultados: {len(results)}")
        return results

    except Exception as exc:
        logger.error(f"Error en task search_phone_task: {exc}")
        # Reintentar después de 60 segundos
        raise self.retry(exc=exc, countdown=60)


async def import_ignorant_modules():
    """Importar módulos ignorant dinámicamente."""

    def import_submodules(package, recursive=True):
        if isinstance(package, str):
            package = importlib.import_module(package)
        results = {}
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
            full_name = package.__name__ + "." + name
            results[full_name] = importlib.import_module(full_name)
            if recursive and is_pkg:
                results.update(import_submodules(full_name))
        return results

    modules = import_submodules("ignorant.modules")
    websites = []

    for module_name in modules:
        if len(module_name.split(".")) > 3:
            modu = modules[module_name]
            site = module_name.split(".")[-1]
            if site in modu.__dict__:
                websites.append(modu.__dict__[site])

    logger.debug(f"Importados {len(websites)} módulos ignorant")
    return websites


async def search_phone_async(phone, country_code):
    """Ejecutar búsqueda usando módulos ignorant asíncronamente."""
    websites = await import_ignorant_modules()
    results = []

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            follow_redirects=True,
        ) as client:
            for website in websites:
                try:
                    await website(phone, country_code, client, results)
                    logger.debug(f"Módulo {website.__name__} completado")
                except Exception as e:
                    logger.warning(f"Error con módulo {website.__name__}: {e}")
                    results.append(
                        {
                            "name": website.__name__,
                            "domain": f"{website.__name__}.com",
                            "rateLimit": True,
                            "exists": False,
                            "error": str(e)[:100],
                        }
                    )

    except Exception as e:
        logger.error(f"Error durante la búsqueda: {e}")
        raise

    return results


@shared_task
def test_celery():
    """Task de prueba para verificar que Celery funciona."""
    logger.info("Test task ejecutada exitosamente")
    return {"status": "success", "message": "Celery está funcionando"}
