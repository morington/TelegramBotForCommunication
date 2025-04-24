import argparse
import base64
import sys
from pathlib import Path


def encode_file(input_path: Path) -> None:
    """Encode the contents of a file into a URL-safe Base64 string.

    Args:
        input_path: Path to the file to be encoded.

    Raises:
        SystemExit: If the specified file does not exist.
    """
    if not input_path.exists():
        print(f"❌ File {input_path} not found.")
        sys.exit(1)

    content: str = input_path.read_text()
    encoded: str = base64.urlsafe_b64encode(content.encode()).decode()
    print(f"🔐 Encoded content:\n{encoded}")


def decode_to_file(encoded_key: str, output_path: Path) -> None:
    """Decode a URL-safe Base64 string and write it to a file.

    Args:
        encoded_key: The Base64-encoded string to decode.
        output_path: Path where the decoded file will be written.

    Raises:
        SystemExit: If decoding fails due to invalid input.
    """
    try:
        decoded: str = base64.urlsafe_b64decode(encoded_key.encode()).decode()
        output_path.write_text(decoded)
        print(f"✅ File successfully created: {output_path}")
    except Exception as e:
        print(f"❌ Decoding error: {e}")
        sys.exit(1)


def setup_parser() -> argparse.ArgumentParser:
    """Configure and return an ArgumentParser for CLI functionality."""
    parser = argparse.ArgumentParser(description="🔐 File encoder/decoder utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for 'encode' command
    encode_parser = subparsers.add_parser("encode", help="Encode a file into Base64")
    encode_parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the input file to encode",
    )

    # Subparser for 'decode' command
    decode_parser = subparsers.add_parser("decode", help="Decode a Base64 string into a file")
    decode_parser.add_argument("key", help="The Base64-encoded string to decode")
    decode_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to the output file",
    )

    return parser


def main() -> None:
    """Main entry point for the file encoding/decoding utility."""
    parser: argparse.ArgumentParser = setup_parser()
    args: argparse.Namespace = parser.parse_args()

    if args.command == "encode":
        encode_file(args.input)
    elif args.command == "decode":
        decode_to_file(args.key, args.output)


if __name__ == "__main__":
    main()
