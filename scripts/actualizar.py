#!/usr/bin/env python3
"""Lee los productos de la tienda WooCommerce de Lavanda & Tilo (API pública Store API)
y genera productos.json para el catálogo. Uso:
  python3 scripts/actualizar.py                  -> descarga de la tienda
  python3 scripts/actualizar.py --desde raw.json -> usa un JSON ya descargado
Si la descarga falla o trae muy pocos productos, NO pisa el productos.json existente."""
import json, sys, re, html, time, urllib.request, datetime, os

TIENDA = "https://lavandatilo.com.ar"
API = TIENDA + "/wp-json/wc/store/v1/products?per_page=100&page={}"
SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "productos.json")
# Categorías principales (las de la tienda en mayúsculas), en el orden del menú
PRINCIPALES = ["DECO", "BAZAR", "TEXTIL", "BAÑO", "BEAUTY", "LAVANDA&TILO DESIGN", "ACCESORIOS MODA", "DECO INFANTIL"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def descargar():
    todos = []
    for pagina in range(1, 20):
        for intento in range(3):
            try:
                req = urllib.request.Request(API.format(pagina), headers={"User-Agent": UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    lote = json.loads(r.read().decode("utf-8"))
                break
            except Exception as e:
                print(f"Página {pagina}, intento {intento + 1}: {e}", file=sys.stderr)
                time.sleep(5 * (intento + 1))
        else:
            raise SystemExit("No se pudo leer la tienda; se conserva el catálogo anterior.")
        if not isinstance(lote, list):
            raise SystemExit("Respuesta inesperada de la tienda; se conserva el catálogo anterior.")
        todos += lote
        if len(lote) < 100:
            break
    return todos


def texto(h):
    h = re.sub(r"<br\s*/?>|</p>|</li>", "\n", h or "", flags=re.I)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    return "\n".join(l.strip() for l in h.splitlines() if l.strip())


def img(i):
    return {"t": i.get("thumbnail") or i["src"], "g": i["src"]}


def transformar(raw):
    out = []
    for p in raw:
        pr = p["prices"]
        cats = [html.unescape(c["name"]) for c in p.get("categories", [])]
        principal = [c for c in cats if c.upper() in PRINCIPALES]
        rango = pr.get("price_range")
        out.append({
            "id": p["id"],
            "n": html.unescape(p["name"]),
            "u": p["permalink"],
            "p": int(pr["price"] or 0),
            "pr": int(pr["regular_price"] or 0),
            "min": int(rango["min_amount"]) if rango else None,
            "max": int(rango["max_amount"]) if rango else None,
            "oferta": bool(p.get("on_sale")),
            "stock": bool(p.get("is_in_stock")),
            "st": texto((p.get("stock_availability") or {}).get("text", "")),
            "cat": [c.upper() for c in principal] or ["OTROS"],
            "sub": [c for c in cats if c.upper() not in PRINCIPALES],
            "d": texto(p.get("short_description")) or texto(p.get("description"))[:600],
            "dl": texto(p.get("description"))[:1500],
            "a": [{"n": a["name"], "v": [html.unescape(t["name"]) for t in a.get("terms", [])]}
                  for a in p.get("attributes", []) if a.get("terms")],
            "dim": p.get("formatted_dimensions") if p.get("formatted_dimensions") not in ("", "N/D", "N/A") else "",
            "img": [img(i) for i in p.get("images", [])[:6]],
        })
    out.sort(key=lambda x: (not x["stock"], x["n"].lower()))
    return out


def main():
    if "--desde" in sys.argv:
        raw = json.load(open(sys.argv[sys.argv.index("--desde") + 1], encoding="utf-8"))
    else:
        raw = descargar()
    prods = transformar(raw)
    if len(prods) < 20:
        raise SystemExit(f"Solo llegaron {len(prods)} productos; se conserva el catálogo anterior.")
    # Si los productos no cambiaron, no se toca el archivo (evita commits vacíos)
    if os.path.exists(SALIDA):
        try:
            if json.load(open(SALIDA, encoding="utf-8")).get("productos") == prods:
                print("Sin cambios en la tienda.")
                return
        except Exception:
            pass
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    json.dump({"actualizado": ahora.strftime("%d/%m/%Y %H:%M"), "tienda": TIENDA, "productos": prods},
              open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(prods)} productos ({sum(p['stock'] for p in prods)} con stock) -> productos.json")


if __name__ == "__main__":
    main()
