from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).resolve().parent

RECEIPTS = [
    {
        "name": "receiptAtb.png",
        "lines": [
            "ATB Market",
            "15.03.2024",
            "Khleb 45.00",
            "Moloko 89.90",
            "ITOGO: 134.90 UAH",
        ],
    },
    {
        "name": "receiptSilpo.png",
        "lines": [
            "Silpo",
            "01/04/2024",
            "Coffee 120.00",
            "TOTAL: 120.00 грн",
        ],
    },
    {
        "name": "receiptDollar.png",
        "lines": [
            "Corner Shop",
            "2024-05-10",
            "Snack 3.50",
            "TOTAL: $12.99",
        ],
    },
    {
        "name": "receiptEuro.png",
        "lines": [
            "Cafe Roma",
            "12 March 2024",
            "Latte 4.50",
            "Summe: 4,50 EUR",
        ],
    },
    {
        "name": "receiptHryvnia.png",
        "lines": [
            "Varus",
            "20.06.2024",
            "Water 25.00",
            "Разом 250,00 ₴",
        ],
    },
    {
        "name": "receiptBlurry.png",
        "lines": ["Blurry Shop", "ITOGO: 10.00"],
        "blur": True,
    },
    {
        "name": "receiptEmpty.png",
        "lines": ["###", "???", "@@@"],
    },
    {
        "name": "receiptMultiAmount.png",
        "lines": [
            "Pyaterochka",
            "08.07.2024",
            "ItemA 45.00",
            "ItemB 89.90",
            "ItemC 12.00",
            "ITOGO: 146.90 RUB",
        ],
    },
]


def font() -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for candidate in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), 28)
    return ImageFont.load_default()


def render_receipt(lines: list[str], blur: bool = False) -> Image.Image:
    width, line_height, padding = 700, 40, 40
    height = padding * 2 + line_height * len(lines)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    text_font = font()
    y = padding
    for line in lines:
        draw.text((padding, y), line, fill="black", font=text_font)
        y += line_height
    if blur:
        image = image.resize((width // 8, height // 8)).resize((width, height))
    return image


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for receipt in RECEIPTS:
        image = render_receipt(receipt["lines"], blur=receipt.get("blur", False))
        target = FIXTURES_DIR / receipt["name"]
        image.save(target)
        print(f"wrote {target}")


if __name__ == "__main__":
    main()
