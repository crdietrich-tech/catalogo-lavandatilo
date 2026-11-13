# Catálogo online · Lavanda & Tilo

Catálogo web (GitHub Pages) con fotos, precios, variantes y stock de lavandatilo.com.ar.

- `productos.json` se regenera solo cada 3 horas con la Action **Actualizar catálogo desde la tienda** (`.github/workflows/actualizar-catalogo.yml`), que lee la API pública de WooCommerce.
- Para forzar una actualización: pestaña **Actions** → *Actualizar catálogo desde la tienda* → **Run workflow**.
- Número de WhatsApp para consultas: editar `whatsapp` en `index.html` (`window.CONFIG`).
- Las fotos se muestran directo desde la tienda, así que cualquier cambio de foto también se refleja.
