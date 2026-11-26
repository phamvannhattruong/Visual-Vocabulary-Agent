"""Export the bundled YOLO11n checkpoint for CPU inference."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    model_dir = Path(__file__).resolve().parents[2] / "backend" / "resources" / "models"
    checkpoint = model_dir / "yolo11n.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Missing bundled YOLO11n checkpoint: {checkpoint}")

    with TemporaryDirectory() as config_dir:
        os.environ["YOLO_CONFIG_DIR"] = config_dir
        from ultralytics import YOLO

        YOLO(str(checkpoint)).export(
            format="onnx", imgsz=640, dynamic=True, simplify=False, opset=17, nms=False, device="cpu"
        )


if __name__ == "__main__":
    main()
