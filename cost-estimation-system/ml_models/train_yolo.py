"""
YOLOv8 training script for BOM-Dataset-v4.
This script sets up the training pipeline to fine-tune a YOLOv8 object detection
model on the custom visual dataset.
"""
import os

try:
    from ultralytics import YOLO
except ImportError:
    print("ultralytics not installed. Install with: pip install ultralytics")

def train_vision_model():
    base_dir = os.path.dirname(__file__)
    costing_dir = os.path.abspath(os.path.join(base_dir, '..', 'Costing'))
    dataset_dir = os.path.join(costing_dir, "BOM-Dataset-v4")
    if not os.path.exists(dataset_dir):
        print(f"Dataset directory not found: {dataset_dir}")
        return 

    # Check if a data.yaml exists, if not we create one dynamically
    yaml_path = os.path.join(dataset_dir, 'data.yaml')
    if not os.path.exists(yaml_path):
        print(f"Creating a default data.yaml at {yaml_path}")
        with open(yaml_path, 'w') as f:
            f.write(f"path: {dataset_dir}\n")
            f.write("train: images/train\n")
            f.write("val: images/val\n")
            f.write("names:\n")
            f.write("  0: table\n")
            f.write("  1: title_block\n")
            f.write("  2: dimension\n")
            f.write("  3: view\n")

    print("Initializing YOLOv8 model for training...")
    # Load a pretrained model
    try:
        model = YOLO('yolov8n.pt') 
        
        # Train the model
        print("Starting training...")
        results = model.train(data=yaml_path, epochs=10, imgsz=640)
        print("Training complete!")
        print(results)
    except Exception as e:
        print(f"Training failed or ultralytics not available: {e}")

if __name__ == "__main__":
    # Note: Running this on CPU could take a while.
    # train_vision_model()
    print("YOLO Training Script ready. Uncomment train_vision_model() to run.")
    