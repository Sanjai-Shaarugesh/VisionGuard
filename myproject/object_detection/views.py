# object_detection/views.py

import os
import torch
from torchvision import models, transforms
from PIL import Image
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.core.files.storage import default_storage
from django.conf import settings
import logging
from io import BytesIO

# Initialize logging
logger = logging.getLogger(__name__)

# Load the pretrained Faster R-CNN model once when the server starts
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.to(device)
model.eval()

# Define the preprocessing pipeline
preprocess = transforms.Compose([
    transforms.ToTensor(),
])

# COCO label names for common objects
COCO_INSTANCE_CATEGORY_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat','cell_phone','mobile_phone',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
    'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog',
    'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush','shirt'
]

class ImageUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        try:
            # Check if 'image' is in the uploaded files
            if 'image' not in request.FILES:
                return Response({"error": "No image provided."}, status=400)

            # Get the uploaded image file (video frame)
            image_file = request.FILES['image']

            # Open the image from the in-memory file
            img = Image.open(BytesIO(image_file.read())).convert("RGB")

            # Preprocess the image
            img_tensor = preprocess(img).unsqueeze(0).to(device)  # Add batch dimension

            # Perform object detection
            with torch.no_grad():
                prediction = model(img_tensor)

            # Extract detection data (labels)
            labels = prediction[0]['labels'].cpu().numpy().tolist()

            # Debug logging
            logger.info(f"Labels: {labels}")
            logger.info(f"Valid range: {0} to {len(COCO_INSTANCE_CATEGORY_NAMES) - 1}")

            # Ensure labels are within the correct range
            label_names = []
            for label in labels:
                if 0 <= label < len(COCO_INSTANCE_CATEGORY_NAMES):
                    label_names.append(COCO_INSTANCE_CATEGORY_NAMES[label])
                else:
                    logger.warning(f"Label {label} is out of range")

            # Return the detected labels
            return Response({
                "labels": label_names,
            })

        except Exception as e:
            logger.exception("Error during video frame processing.")
            return Response({"error": "Video frame processing failed."}, status=500)
