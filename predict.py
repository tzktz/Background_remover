import os
import shutil
import zipfile
from cog import BasePredictor, Input, Path
from PIL import Image
from rembg import remove, new_session
import tempfile
import pyheif

u2net = "u2net"
u2net_human_seg = "u2net_human_seg"
u2net_cloth_seg = "u2net_cloth_seg"
u2netp = "u2netp"


class Predictor(BasePredictor):
    def predict(
            self, input_image_path: Path = Input(description="Upload single image or zip folder", default=None),
            model: str = Input(description="select model",
                               choices=["u2net", "u2net_human_seg", "u2net_cloth_seg", "u2netp"],
                               default="u2net_human_seg"),
    ) -> Path:
        if not input_image_path:
            raise ValueError("No input image selected")

        # Choose the model
        selected_model = None
        if model == "u2net":
            selected_model = u2net
        elif model == "u2net_human_seg":
            selected_model = u2net_human_seg
        elif model == "u2net_cloth_seg":
            selected_model = u2net_cloth_seg
        elif model == "u2netp":
            selected_model = u2netp
        else:
            raise ValueError(f"Invalid model selected: {model}")

        model_name = selected_model
        print(f"Using model: {model_name}")
        session = new_session(model_name)

        # Check if the input is a zip file
        if input_image_path.suffix == ".zip":
            # Unzip the folder
            unzip_folder = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(input_image_path, 'r') as zip_ref:
                zip_ref.extractall(unzip_folder)

            # Process images in the unzipped folder and its subfolders
            output_folder = Path(tempfile.mkdtemp())
            self.process_zip_contents(unzip_folder, model_name, output_folder)

            # Zip the output folder
            result_zip_path = Path(tempfile.mkdtemp()) / "background_removed_images.zip"
            shutil.make_archive(result_zip_path.with_suffix(""), 'zip', output_folder)

            # Clean up temporary folders
            shutil.rmtree(unzip_folder)
            shutil.rmtree(output_folder)

            print(f"Result saved to: {result_zip_path}")
            return result_zip_path
        else:
            # Process a single image
            output_folder = Path(tempfile.mkdtemp())
            output_path = self.process_image(input_image_path, model_name, output_folder)
            print(f"Result saved to: {output_path}")
            return output_path

    def process_zip_contents(self, folder, model, output_folder):
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = Path(root) / file
                self.process_image(file_path, model, output_folder)

    def process_image(self, input_image_path, model, output_folder):
        print(f"Reading input image from: {input_image_path}")

        # Check if the image is a HEIF file
        if input_image_path.suffix.lower() == ".heif":
            heif_file = pyheif.read(input_image_path)
            input_image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode,
                heif_file.stride,
            )
        else:
            # Open the image and convert it to RGBA mode (including an alpha channel)
            input_image = Image.open(input_image_path).convert("RGBA")

        print("Removing background...")
        output_image = remove(input_image, session=new_session(model))

        # Save the result in the output folder with a transparent background
        output_path = output_folder / f"{input_image_path.stem}_background_removed.png"
        output_image.save(output_path)

        print(f"Result saved to: {output_path}")
        return output_path
