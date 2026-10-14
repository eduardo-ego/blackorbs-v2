# A4 — Licencia y URL pública del proyecto

## URL del repositorio

- El remote real configurado en este checkout es:
  **`https://github.com/eduardo-ego/blackorbs_device.git`** (`git remote -v`, remote `origin`).
- **`github.com/eduardo-ego/aiot_ciateq` NO es correcta** — es un nombre distinto al remote
  configurado en el propio dispositivo.
- Se intentó confirmar vía API pública de GitHub (`api.github.com/repos/...`) para ambos nombres:
  ambos devuelven `404 Not Found`. Esto significa una de dos cosas (no se puede distinguir desde
  aquí sin autenticación): el repositorio es **privado**, o el nombre/usuario no existe tal cual en
  GitHub. **Acción para el autor:** confirmar manualmente en la cuenta de GitHub cuál es la URL
  pública definitiva (posiblemente haya que hacerlo público, o la URL correcta usa otro
  usuario/organización).

## Licencia

- **No existe archivo de licencia en el repositorio** (`LICENSE`, `LICENSE.md`, `LICENSE.txt`,
  `COPYING*` — ninguno presente en la raíz ni en el historial de git: `git log --all -- LICENSE*`
  no devuelve commits).
- El único campo de licencia encontrado es `"license": "ISC"` dentro de `api/package.json`, que solo
  aplica (por convención de npm) al paquete `api/` en sí (metadato de `package.json`, heredado del
  template por defecto de `npm init`), **no** es una declaración de licencia del proyecto completo
  ni está respaldada por un archivo `LICENSE` con el texto correspondiente.
- **Conclusión para el artículo:** a la fecha de esta extracción, el proyecto **no tiene una
  licencia formalmente declarada** a nivel de repositorio. Si el artículo va a declarar una licencia
  (p. ej. para reproducibilidad / disponibilidad de código), el autor debe añadir explícitamente un
  archivo `LICENSE` al repo antes de publicar esa afirmación.
