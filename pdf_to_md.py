#!/opt/homebrew/anaconda3/envs/pdf_to_md/bin/python
"""
This script converts a PDF file to a Markdown file using GPT-4 visual reasoning.

The script takes an input PDF file path as an argument and produces a Markdown
file in the same directory with the same name as the PDF file.
"""
import argparse
import base64
import io
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
from tqdm import tqdm
from typing import List, Union

# Setup OpenAI client
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)


def pdf_to_markdown(
        pdf_path: str, 
        output_dir: str,
        mode: str = "v",
        verbose: bool = True
    ) -> str:
    """
    Main function to convert a PDF to Markdown using GPT-4 visual reasoning.

    This function takes a path to a PDF file, an output directory, a mode
    indicating whether to use 'vision-only' (v) or 'vision-and-text' (vt) 
    processing, and a verbose flag. It converts the PDF to images, processes 
    each image with GPT-4 to generate markdown text, and writes the markdown 
    text to a file with the same name as the PDF file but with a .md extension, 
    located in the output directory. If verbose is True, it also prints the 
    markdown text to the screen.

    Args:
        pdf_path: The path to the input PDF file.
        output_dir: The directory where the output markdown file will be saved.
        mode: The processing mode ('v' for vision-only, 'vt' for 
            vision-and-text).
        verbose: If True, print the markdown text to the screen.

    Returns:
        output_file_path
    """
    # Setup constants and validation
    output_file_name = os.path.basename(pdf_path).rsplit('.', 1)[0] + '.md'
    output_file_path = os.path.join(output_dir, output_file_name)

    # Validate mode
    valid_modes = ['v', 'vt']
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid mode '{mode}'. Valid modes are {valid_modes}."
        )

    # Get images
    images = _pdf_to_images_with_storage(pdf_path, output_dir)

    # Get prior texts
    if mode == 'v':
        prior_texts = [None] * len(images)
    elif mode == 'vt':
        prior_texts = _get_prior_text(pdf_path)

    # Check that lengths match
    if len(prior_texts) != len(images):
        raise ValueError(
            f"The number of prior texts ({len(prior_texts)}) does not match "
            f"the number of images ({len(images)})."
        )

    # Build the markdown
    markdown_content = []
    for image, prior_text in tqdm(zip(images, prior_texts)):
        image_base64 = _pdf_image_to_base64_str(image)
        markdown_text = _process_image_with_gpt4(image_base64, prior_text)
        markdown_content.append(markdown_text)
        if verbose:
            print(markdown_text)

    # Write results
    with open(output_file_path, 'w') as file:
        file.write('\n'.join(markdown_content))

    return output_file_path


@retry(
        wait=wait_random_exponential(min=1./5000, max=5), 
        stop=stop_after_attempt(3)
)
def _process_image_with_gpt4(
        image_base64: str, 
        prior_text: Union[str, None] = None
    ) -> str:
    """
    Send a base64-encoded image to GPT-4 for processing, optionally including
    prior text for context.

    Constructs a prompt for GPT-4 to interpret the image as a Markdown document,
    preserving the semantic meaning and information hierarchy, including tables.
    If prior text is provided, it is included to assist GPT-4 in the interpretation.

    Args:
        image_base64: The base64-encoded image to be processed.
        prior_text: Optional; previously extracted text to provide context.

    Returns:
        The Markdown version of the image content as interpreted by GPT-4.
    """
    vision_base = (
        "Write a Markdown version of this page keeping as much of the semantic "
        "meaning from information hierarchy as possible. For tabular-like "
        "data (including chart data), make easy to read tables as they'd be "
        "presented by a financial analyst."
    )

    vision_assist = (
        "\n\nYour vision isn't great, so I've provided previously extracted "
        "text to help in <prior_text> tags. That text isn't perfect either so "
        "use a balanced approach to create the full Markdown output.\n"
        "\n<prior_text>\n{prior_text}\n</prior_text>\n"
    )

    prompt = f"{vision_base}{vision_assist}" if prior_text else vision_base
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"    
                        }
                    }

                ]
            }
        ],
        max_tokens=4096
    )
    return response.choices[0].message.content


def _pdf_to_images_with_storage(
        pdf_path: str, 
        output_dir: str
    ) -> List[Image.Image]:
    """
    Load images from the output directory if they exist, otherwise convert the 
    PDF to images and save them to the specified output directory.

    Args:
        pdf_path: The path to the input PDF file.
        output_dir: The directory where the output images will be saved.

    Returns:
        A list of PIL Image objects.
    """
    base_name = os.path.basename(pdf_path).rsplit('.', 1)[0]
    image_folder = os.path.join(output_dir, base_name + '_images')
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            image.save(os.path.join(image_folder, f'{base_name}_image_{i}.png'))
    else:
        images = [
            Image.open(os.path.join(image_folder, f)) 
            for f in os.listdir(image_folder) if f.endswith('.png')
        ]
    return images


def _get_prior_text(pdf_path: str) -> List[str]:
    """
    Extracts simple text from each page of the PDF using PyPDF2.

    Args:
        pdf_path (str): The path to the input PDF file.

    Returns:
        List[str]: A list of strings where each string represents the extracted 
            text from a single page of the PDF.
    """
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text_list = [page.extract_text() for page in reader.pages]
    return text_list


def _pdf_image_to_base64_str(pdf_page: Image) -> str:
    """
    Convert a PDF page to a base64 encoded JPEG image.

    Args:
        pdf_page (Image): A PIL Image object representing a PDF page.

    Returns:
        str: A base64 encoded string of the JPEG image.
    """
    image_buffer = io.BytesIO()
    pdf_page.save(image_buffer, format='JPEG')
    byte_data = image_buffer.getvalue()
    return base64.b64encode(byte_data).decode('utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a PDF to a Markdown file using GPT-4 visual reasoning."
    )
    parser.add_argument(
        'target_path', 
        type=str, 
        help="The path to the input PDF file or directory containing PDF files."
    )
    parser.add_argument(
        '-o', '--output_dir',
        type=str,
        default=None,
        help="The directory to the output files. If not specified, defaults to the same location as the PDF file."
    )
    parser.add_argument(
        '-m', '--mode', 
        type=str, 
        default='vt', 
        choices=['v', 'vt'],
        help="Toggle between 'v' for vision-only and 'vt' (default) for vision-and-text processing."
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help="If set, print the markdown text to the screen."
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=False,
        help="If set, treat the target path as a directory and process all PDF files within it recursively."
    )
    parser.add_argument(
        '-p', '--parallel',
        action='store_true',
        default=False,
        help="If set, process each PDF file in parallel when using recursive mode."
    )
    args = parser.parse_args()
    target_path = args.target_path
    processing_mode = args.mode
    output_dir = args.output_dir
    verbose = args.verbose
    recursive = args.recursive
    parallel = args.parallel

    def process_pdf(pdf_path: str, output_dir: str, processing_mode: str, verbose: bool):
        out = pdf_to_markdown(pdf_path, output_dir, processing_mode, verbose)
        print(f"Output file: {out}")

    if recursive:
        if not os.path.isdir(target_path):
            print(f"Error: The path '{target_path}' is not a directory.")
            sys.exit(1)
        if parallel:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                futures = []
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_path = os.path.join(root, file)
                            output_dir = args.output_dir or os.path.dirname(pdf_path)
                            futures.append(executor.submit(process_pdf, pdf_path, output_dir, processing_mode, verbose))
                for future in futures:
                    future.result()
        else:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_path = os.path.join(root, file)
                        output_dir = args.output_dir or os.path.dirname(pdf_path)
                        process_pdf(pdf_path, output_dir, processing_mode, verbose)
    else:
        if not os.path.isfile(target_path):
            print(f"Error: The file '{target_path}' does not exist.")
            sys.exit(1)
        output_dir = args.output_dir or os.path.dirname(target_path)
        process_pdf(target_path, output_dir, processing_mode, verbose)
