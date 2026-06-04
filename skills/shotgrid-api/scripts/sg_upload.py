"""Tool: shotgrid-api__sg_upload — Upload a file to ShotGrid."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_upload
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Upload a file to ShotGrid and attach it to an entity field.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to attach the file to (e.g., Version, Shot)")
    parser.add_argument("--entity-id", type=int, required=True, help="ID of the entity to attach the file to")
    parser.add_argument("--field-name", type=str, required=True, help="Name of the file field on the entity (e.g., sg_uploaded_movie)")
    parser.add_argument("--file-path", type=str, required=True, help="Local path to the file to upload")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_upload(
            sg,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            field_name=args.field_name,
            file_path=args.file_path,
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
