
# PDF to Markdown Converter

This tool converts PDF documents to Markdown files using GPT-4's visual reasoning capabilities. It's designed to accurately interpret and transcribe the contents of a PDF, including text and tabular data, into a Markdown format. This script is particularly useful for processing and digitizing documents for easier editing and sharing in a text-based format.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3
- Pip (Python package installer)
- [An OpenAI API key](https://beta.openai.com/signup/) for GPT-4 access

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/scottkwong/pdf-to-md.git
cd pdf_to_md
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

If you don't have `poppler` installed, see [Additional Dependencies](#additional-dependencies).

Set your OpenAI API key in your environment or `.env` file as `OPENAI_API_KEY`.


## Script Configuration

Before running `pdf_to_md.py`, ensure the shebang line (first line in the file) points to your Python interpreter. If needed, replace `#!/opt/homebrew/anaconda3/envs/pdf_to_md/bin/python` with the path to your Python executable, which you can find with `which python` or `which python3` in your terminal.


## Usage

To use the script, you'll need to provide the path to the PDF file you want to convert. The script also supports various options, including specifying an output directory, choosing the processing mode (vision-only or vision-and-text), and a verbose mode for additional output details.

Basic usage:

```bash
./pdf_to_md.py <path_to_pdf>
```

Advanced usage with options:

```bash
./pdf_to_md.py <path_to_pdf> -o <output_directory> -m <mode> -v
```

Where:
- `<path_to_pdf>` is the path to your PDF file.
- `<output_directory>` is the directory where the Markdown file will be saved (optional, defaults to the PDF's directory).
- `<mode>` is either 'v' for vision-only or 'vt' for vision-and-text (optional, defaults to 'vt').
- `-v` or `--verbose` prints the markdown text to the screen (optional).

## License

This project is open source and available under the [MIT License](LICENSE.txt).


## Additional Dependencies

Aside from the Python packages listed in `requirements.txt`, this project requires `poppler-utils` to be installed on your system. `poppler-utils` includes utilities like `pdftoppm` which are essential for PDF processing.

### Installing poppler-utils

#### On Ubuntu/Debian-based Linux Distributions:

Run the following command in your terminal:

```bash
sudo apt-get install -y poppler-utils
```

#### On macOS:

If you have Homebrew installed, you can run:

```bash
brew install poppler
```

If you do not have Homebrew, you can install it from [here](https://brew.sh/).

### Verifying the Installation

To ensure that `poppler-utils` has been installed correctly, you can run:

```bash
pdftoppm -v
```

This command should return the version of `pdftoppm` if `poppler-utils` is installed correctly.
