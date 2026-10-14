# C5 — Commit del cambio a duty-cycle en display/ring_display.py

**No existe tal commit.** Verificado con:

```
git log --oneline --all -- display/ring_display.py display/config.py
```

(sin salida — ningún commit en ningún branch toca esos archivos).

## Hallazgo más importante detrás de esto

El repositorio git de este checkout tiene su raíz en `/home/blackorbs` (no en
`/home/blackorbs/blackorbs-v2` — confirmado con `git rev-parse --show-toplevel`), y
**`blackorbs-v2/` completo (api/, ml/, sensor/, display/) no tiene ni un solo archivo bajo control
de versiones** (`git ls-files | grep blackorbs-v2` no devuelve nada). Los dos únicos commits del
repo ("first commit", "script temp") solo contienen archivos sueltos del `$HOME` (`.bash_history`,
caché de `pip`), aparentemente por un `git init` hecho por accidente en el home en vez de dentro del
proyecto.

**Consecuencia práctica:** aunque `git remote -v` apunta a
`github.com/eduardo-ego/blackorbs_device.git` (ver `A4_licencia_url.md`), un `git push` desde este
estado **no subiría el código del proyecto** — subiría archivos del home. El código fuente de v2 no
tiene historial de versiones recuperable en este dispositivo; el cambio a duty-cycle (evidenciado
empíricamente en `C_selfheating_tabla.md`/`C_fig9_selfheating_serie.png`, y documentado en el
comentario de `display/config.py`) se hizo directo sobre el archivo sin commit.

**Recomendación para el autor:** si se quiere preservar el historial real de v2 (y poder citar
commits en el artículo), hay que inicializar un repo git dentro de `blackorbs-v2/` (o mover el
`.git` actual) y hacer un primer commit del estado presente antes de seguir editando código.
