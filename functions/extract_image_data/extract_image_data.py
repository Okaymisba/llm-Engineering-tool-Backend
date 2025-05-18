from PIL import Image
from pytesseract import pytesseract
from ultralytics import YOLO


def extract_image_data(image):
    """
    Extracts textual and object detection data from a given image.

    This function uses the YOLO model for object detection and PyTesseract
    for Optical Character Recognition (OCR) to extract text and detected
    objects from an image. It processes the image input, performs OCR to
    obtain the textual content, and identifies objects detected in the image
    along with their respective labels and confidence scores.

    :param image: The image file path to be processed.

    :return: A dictionary containing two keys:
        - "image_text": The textual content extracted from the image.
        - "detected_objects": A list of dictionaries, where each dictionary
          contains:
            - "label": The label of the detected object.
            - "confidence": The confidence score of the detection, rounded to
              two decimal places.
    """

    model = YOLO("yolov8n.pt")
    image = Image.open(image)
    image_text = pytesseract.image_to_string(image)

    results = model.predict(image)

    detected_objects = []
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            confidence = float(box.conf[0])
            detected_objects.append({
                "label": label,
                "confidence": round(confidence, 2)
            })

    return {"image_text": image_text, "detected_objects": detected_objects}
