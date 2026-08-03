import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "worker" / "src"), str(ROOT / "shared" / "src")]


def main() -> int:
    path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(ROOT / "secrets" / "google-vision.json"),
    )
    print(f"credentials_path={path}")
    file_path = Path(path)
    if not file_path.exists():
        host_hint = ROOT / "secrets" / "google-vision.json"
        print(f"FAIL: файл не найден. Ожидается: {host_hint}")
        return 1

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"FAIL: JSON не читается: {error}")
        return 1

    project = data.get("project_id")
    email = data.get("client_email")
    if not project or not email:
        print("FAIL: в JSON нет project_id / client_email")
        return 1
    print(f"project_id={project}")
    print(f"client_email={email}")

    try:
        from google.cloud import vision
    except ImportError:
        print("FAIL: пакет google-cloud-vision не установлен в этом окружении")
        return 1

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(file_path)
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(
            content=(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
                b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
                b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
            )
        )
        response = client.document_text_detection(image=image)
    except Exception as error:
        print(f"FAIL: вызов Vision API не удался: {error}")
        return 1

    if response.error.message:
        print(f"FAIL: Vision API error: {response.error.message}")
        return 1

    print("OK: Google Vision API отвечает")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())