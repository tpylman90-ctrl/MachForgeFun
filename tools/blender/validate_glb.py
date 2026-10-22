"""Validate the structural integrity of a Blender-exported GLB using stdlib only."""
import json
import pathlib
import struct
import sys


def main(path):
    path = pathlib.Path(path)
    data = path.read_bytes()
    if len(data) < 20:
        raise SystemExit("GLB is too short to contain a header and JSON chunk")
    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total_length != len(data):
        raise SystemExit("Invalid GLB header or length")
    json_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:
        raise SystemExit("The first GLB chunk is not JSON")
    document = json.loads(data[20:20 + json_length].decode("utf-8").rstrip(" \t\r\n\0"))
    meshes = document.get("meshes", [])
    nodes = document.get("nodes", [])
    materials = document.get("materials", [])
    if not meshes or len(nodes) < 10:
        raise SystemExit(f"Range asset is incomplete: {len(meshes)} meshes, {len(nodes)} nodes")
    if not materials:
        raise SystemExit("Range asset has no exported materials")
    print(f"Valid GLB: {path} | {len(meshes)} meshes | {len(nodes)} nodes | {len(materials)} materials")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "artifacts/machforge_range.glb")
