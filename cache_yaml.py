import os
import json
import tempfile
import hashlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.constructor.ignore_aliases = True


def _str_constructor(loader, node):
    if node.tag == 'tag:yaml.org,2002:bool' and node.value == 'y':
        return 'y'
    return loader.construct_scalar(node)


# Prevent yaml from parsing "y" as True
yaml.constructor.add_constructor('tag:yaml.org,2002:bool', _str_constructor)

temp_folder_path = os.path.join(tempfile.gettempdir(), 'UnityAnimationPlayer_python')
os.makedirs(temp_folder_path, exist_ok=True)


def _get_file_sha256(file_path):
    """Calculate the SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to avoid memory issues with large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


def _save_cache_metadata(json_path, sha256_hash):
    """Save cache metadata (SHA256 hash)"""
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'w') as f:
            json.dump({'sha256': sha256_hash}, f)
    except Exception as e:
        print(f"[Warning]Failed to save cache metadata: {e}")


def _load_cache_metadata(json_path):
    """Load cache metadata"""
    metadata_path = json_path + '.metadata'
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_yaml(path: str, cache=True):
    """Load and cache yaml, using SHA256 to verify file consistency"""
    # Build cache json path
    json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')

    # Calculate SHA256 of source file
    source_sha256 = _get_file_sha256(path)
    if source_sha256 is None:
        raise FileNotFoundError(f"Source file not found: {path}")

    try:
        # Check if cache exists and is valid
        metadata = _load_cache_metadata(json_path)

        if (metadata and
                metadata.get('sha256') == source_sha256 and
                os.path.exists(json_path)):

            # Cache is valid, read directly
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[DEBUG]Loaded cached data for: {path}")
            return data
        else:
            # Cache is invalid or doesn't exist, regenerate
            print(f"[WARNING]Cache invalid or missing, regenerating for: {path}")
            raise FileNotFoundError("Cache needs regeneration")

    except (FileNotFoundError, json.JSONDecodeError):
        # Cache file doesn't exist or is corrupted, regenerate
        with open(path, 'r', encoding='utf-8') as y:
            data = yaml.load(y)

        if cache:
            # Ensure directory exists
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

            # Save JSON cache
            with open(json_path, 'w', encoding='utf-8') as j:
                json_data = json.dumps(data, ensure_ascii=False, indent=2)
                j.write(json_data)

            # Save metadata (SHA256)
            _save_cache_metadata(json_path, source_sha256)
            print(f"[DEBUG]Cached data regenerated for: {path}")

        return json.loads(json.dumps(data))


def clear_yaml_cache(path: str = None):
    """Clear YAML cache files"""
    if path:
        # Clear cache for specific file
        json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')
        metadata_path = json_path + '.metadata'

        for cache_path in [json_path, metadata_path]:
            try:
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    print(f"[DEBUG]Removed cache: {cache_path}")
            except Exception as e:
                print(f"[ERROR]Error removing cache {cache_path}: {e}")
    else:
        # Clear all cache
        import shutil
        try:
            if os.path.exists(temp_folder_path):
                shutil.rmtree(temp_folder_path)
                os.makedirs(temp_folder_path, exist_ok=True)
                print("[DEBUG]Cleared all YAML cache")
        except Exception as e:
            print(f"[ERROR]Error clearing cache: {e}")


def get_cache_info(path: str):
    """Get cache information"""
    json_path = os.path.join(temp_folder_path, path.rsplit('.', 1)[0] + '.json')
    metadata = _load_cache_metadata(json_path)
    source_sha256 = _get_file_sha256(path)

    cache_exists = os.path.exists(json_path)
    metadata_exists = metadata is not None
    is_valid = metadata and metadata.get('sha256') == source_sha256

    return {
        'source_sha256': source_sha256,
        'cached_sha256': metadata.get('sha256') if metadata else None,
        'cache_exists': cache_exists,
        'metadata_exists': metadata_exists,
        'is_valid': is_valid,
        'json_path': json_path
    }