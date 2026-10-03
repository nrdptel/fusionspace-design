"""Screenshot an HTML file to PNG for review previews. Uses Playwright if it is installed, else a headless Chrome/Chromium
binary if one is found, else LibreOffice. Returns False (and the caller falls back to an iframe) when none is available."""
import os, shutil, subprocess, tempfile

CHROMES = ["chromium", "chromium-browser", "google-chrome", "/opt/pw-browsers/chromium",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium"]

def _office_png(html_path, dest):
    """Last resort: LibreOffice renders the page to PDF, pdftoppm rasterises it, and the result is cropped to the content.
    Rougher than a browser (its own HTML layout), but shows what's there."""
    office = shutil.which("soffice") or shutil.which("libreoffice"); ppm = shutil.which("pdftoppm")
    if not (office and ppm): return False
    from PIL import Image, ImageOps
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([office, "--headless", "--convert-to", "pdf:writer_web_pdf_Export", "--outdir", td, html_path],
                       check=True, capture_output=True, timeout=120)
        pdfs = [f for f in os.listdir(td) if f.endswith(".pdf")]
        if not pdfs: return False
        subprocess.run([ppm, "-png", "-r", "110", "-f", "1", "-l", "1", os.path.join(td, pdfs[0]), os.path.join(td, "p")], check=True, capture_output=True)
        pngs = [f for f in os.listdir(td) if f.endswith(".png")]
        if not pngs: return False
        im = Image.open(os.path.join(td, pngs[0])).convert("RGB")
        bb = ImageOps.invert(im.convert("L")).getbbox()
        if bb: im = im.crop((0, 0, min(im.width, bb[2] + 24), min(im.height, bb[3] + 24)))
        im.save(dest)
    return True

def html_png(path, dest, w, h, subst=None):
    src = open(path, encoding="utf-8").read()
    for a, b in (subst or {}).items(): src = src.replace(a, b)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), ".review-shot.html")   # same folder, so relative images resolve
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write('<!doctype html><meta charset="utf-8"><body style="margin:16px;background:#fff">' + src)
    try:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
                pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(300); pg.screenshot(path=dest); b.close()
            return True
        except Exception:
            pass
        exe = next((c for c in CHROMES if shutil.which(c) or os.path.exists(c)), None)
        if not exe: return _office_png(tmp, dest)
        exe = shutil.which(exe) or exe
        subprocess.run([exe, "--headless", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}", f"--screenshot={dest}",
                        "file://" + os.path.abspath(tmp)], check=True, capture_output=True, timeout=60)
        return os.path.exists(dest)
    except Exception:
        return False
    finally:
        if os.path.exists(tmp): os.remove(tmp)
