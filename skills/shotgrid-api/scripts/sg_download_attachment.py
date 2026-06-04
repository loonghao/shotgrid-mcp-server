"""Tool: shotgrid-api__sg_download_attachment — Download an attachment from ShotGrid."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_download_attachment
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Download an attachment from ShotGrid by attachment ID.")
    parser.add_argument("--attachment-id", type=int, required=True, help="ID of the attachment to download")
    parser.add_argument("--output-path", type=str, default=None, help="Optional local path to save the downloaded file")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_download_attachment(
            sg,
            attachment_id=args.attachment_id,
            output_path=args.output_path,
        )
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
