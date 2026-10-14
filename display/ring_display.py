import time

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

from config import I2C_BUS, I2C_ADDR, REFRESCO_SEGUNDOS
from db import ultima_lectura, estado_ml

serial = i2c(port=I2C_BUS, address=I2C_ADDR)
device = ssd1306(serial)
W, H = device.size

FONT = ImageFont.load_default()

CX, CY = W // 2, 24
RADIO_BASE = 15

# Sin animación continua (ver nota en config.py) — el mood se distingue por el
# estilo del aro en cada frame estático, no por movimiento.
ESTILO_POR_MOOD = {
    "happy": {"grosor": 2, "radio_extra": 0, "doble": False},
    "attention": {"grosor": 3, "radio_extra": 2, "doble": False},
    "critical": {"grosor": 3, "radio_extra": 2, "doble": True},
}


def animacion_arranque():
    """Aro formándose desde el centro. Sin texto, sin marca — solo el aro.
    Única secuencia con varios frames seguidos; dura ~0.5s, solo al iniciar."""
    pasos = 18
    for i in range(pasos + 1):
        r = RADIO_BASE * (i / pasos)
        image = Image.new("1", (W, H))
        draw = ImageDraw.Draw(image)
        draw.ellipse((CX - r, CY - r, CX + r, CY + r), outline=255, width=2)
        device.display(image)
        time.sleep(0.03)


def texto_centrado(draw, texto, y):
    bbox = draw.textbbox((0, 0), texto, font=FONT)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), texto, font=FONT, fill=255)


def dibujar_frame(temperatura, humedad, mood):
    estilo = ESTILO_POR_MOOD.get(mood, ESTILO_POR_MOOD["happy"])
    radio = RADIO_BASE + estilo["radio_extra"]

    image = Image.new("1", (W, H))
    draw = ImageDraw.Draw(image)

    draw.ellipse((CX - radio, CY - radio, CX + radio, CY + radio), outline=255, width=estilo["grosor"])
    if estilo["doble"]:
        radio2 = radio + 4
        draw.ellipse((CX - radio2, CY - radio2, CX + radio2, CY + radio2), outline=255, width=1)

    if temperatura is not None and humedad is not None:
        texto = f"{temperatura:.1f}°C   {humedad:.0f}%"
    else:
        texto = "no data"
    texto_centrado(draw, texto, H - 13)

    device.display(image)


def main():
    animacion_arranque()

    while True:
        lectura = ultima_lectura()
        mood = estado_ml()
        temperatura = lectura["temperature"] if lectura else None
        humedad = lectura["humidity"] if lectura else None

        dibujar_frame(temperatura, humedad, mood)

        time.sleep(REFRESCO_SEGUNDOS)


if __name__ == "__main__":
    main()
