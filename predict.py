from cog import BasePredictor, Input, Path
from PIL import Image
from rembg import remove
import tempfile
import zipfile
import os


class Predictor(BasePredictor):
    def predict(self, input_image_path: Path = Input(description="Upload Single Image Or Zip Folder", default=None)) -> Path:
        if not input_image_path:
            raise ValueError("No input image selected")

        print("Input image path:", input_image_path)

        # Create a temporary directory to extract images
        temp_dir = tempfile.mkdtemp()

        # Check if the input is a zip file
        if input_image_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(input_image_path, 'r') as zip_ref:
                # Extract all contents of the zip file
                zip_ref.extractall(temp_dir)

            # Create a directory for processed images
            output_dir = tempfile.mkdtemp()

            # Process each image in the extracted folder
            for root, _, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)

                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        input_image = Image.open(file_path)

                        print("Processing input image:", file_path)

                        output_image = remove(input_image)

                        # Convert the image to RGB mode
                        output_image = output_image.convert("RGB")

                        # Save the processed image in the output directory
                        relative_path = os.path.relpath(file_path, temp_dir)
                        output_path = os.path.join(output_dir, f"output_{relative_path.replace(os.path.sep, '_')}")
                        output_image.save(output_path)

                        print("Image processing complete.")

            # Create a zip file containing the processed images
            output_zip_path = Path(tempfile.mkdtemp()) / "output.zip"
            with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                for root, _, files in os.walk(output_dir):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        zipf.write(file_path, arcname=os.path.relpath(file_path, output_dir))

            print("Output images saved at:", output_zip_path)

            return Path(output_zip_path)

        else:
            # Process a single image
            input_image = Image.open(input_image_path)

            print("Processing input image...")

            output_image = remove(input_image)

            # Convert the image to RGB mode
            output_image = output_image.convert("RGB")

            print("Image processing complete.")

            output_path = Path(tempfile.mkdtemp()) / "output.png"
            output_image.save(output_path)

            print("Output image saved at:", output_path)

            return Path(output_path)
