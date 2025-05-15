from PIL import Image
from pytesseract import pytesseract
from ultralytics import YOLO


def extract_image_data(image_path):
    """
    Extracts text and detected objects from an image using YOLO model and Tesseract OCR library.

    This function opens the given image file, extracts any textual content found in the image using
    the Tesseract OCR library, and uses the YOLO model to identify objects in the image. Identified
    objects contain information about their label and confidence score.

    :param image_path: The file path to the image to process.
    :type image_path: str

    :return: A dictionary with extracted text data and a list of detected objects. Each detected
             object contains a `label` (str) and `confidence` (float) rounded to two decimal places.
    :rtype: dict
    """

    model = YOLO("yolov8n.pt")
    image = Image.open(image_path)
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
