#!/usr/bin/env python3
"""Fritzing part loader — resolve a part's breadboard SVG + pin coordinates.
Each Fritzing .fzp defines connectors; each connector's breadboardView <p> points at an
element id (terminalId/svgId) inside the breadboard SVG = the pin location.
CC-BY-SA parts (credit Fritzing).
"""
import os, glob, xml.etree.ElementTree as ET

REPO = os.environ.get("FZ_REPO") or glob.glob(
    os.path.expanduser("/tmp/gh-clones-*/fritzing-parts"))[0]


def _text(el, default=""):
    return el if isinstance(el, str) else default


def load_part(fzp_path):
    """-> {'svg': path|None, 'pins': {connectorName: elementId}, 'img': ref, 'label': title}"""
    r = ET.parse(fzp_path).getroot()
    title = (r.findtext("title") or os.path.basename(fzp_path)).strip()
    img = None
    for bv in r.iter("breadboardView"):
        for layers in bv.iter("layers"):
            if layers.get("image"):
                img = layers.get("image"); break
        if img:
            break
    svg = None
    if img:
        name = os.path.basename(img)
        c = glob.glob(os.path.join(REPO, "svg", "**", "breadboard", name), recursive=True)
        svg = c[0] if c else None
    pins = {}
    conns = r.find("connectors")
    if conns is not None:
        for c in conns.findall("connector"):
            nm = c.get("name")
            p = c.find(".//breadboardView/p")
            if p is not None and nm:
                pins[nm] = p.get("terminalId") or p.get("svgId")
    return {"svg": svg, "pins": pins, "img": img, "label": title, "fzp": fzp_path}


def find_fzp(term):
    """first core/contrib .fzp whose filename contains term (case-insensitive)"""
    for sub in ("core", "contrib", "user"):
        for f in sorted(glob.glob(os.path.join(REPO, sub, "*.fzp"))):
            if term.lower() in os.path.basename(f).lower():
                return f
    return None


if __name__ == "__main__":
    NEED = {
        "NE555 (DIP-8)": ["ne555", "555_timer", "timer_555", "_555"],
        "resistor": ["resistor.fzp", "resistor_"],
        "LED (bulb)": ["led-5mm", "led_5mm", "5mmled", "LED_"],
        "2N2222 NPN TO-92": ["transistor_signal_NPN_TO92_EBC", "transistor_npn-to92", "to-92"],
        "electrolytic cap": ["electrolytic"],
        "potentiometer": ["rotary_potentiometer", "potentiometer", "trimpot"],
        "Adafruit USB-C MicroLipo": ["micro_lipo", "microlipo", "usb_c_lipo", "lipo_charger", "adafruit_charger"],
    }
    print(f"repo: {REPO}\n")
    for label, terms in NEED.items():
        hit = None
        for t in terms:
            f = find_fzp(t)
            if f:
                p = load_part(f)
                if p["svg"]:
                    hit = p; break
        if hit:
            print(f"OK   {label:26} <- {os.path.basename(hit['fzp'])}")
            print(f"       svg: {os.path.basename(hit['svg'])}  pins: {list(hit['pins'])}")
        else:
            print(f"MISS {label:26} (no fzp with a present breadboard svg)")
