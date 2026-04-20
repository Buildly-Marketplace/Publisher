"""
Annotator Image Utils - Convert annotator avatar to base64 for CSS embedding
"""
import base64
from pathlib import Path

def get_annotator_image_base64(image_path=None):
    """Convert annotator avatar image to base64 for CSS embedding.
    
    Args:
        image_path: Path to the avatar image. Defaults to assets/annotator.png,
                    falls back to assets/bob.png for legacy support.
    """
    if image_path:
        avatar_path = Path(image_path)
    else:
        avatar_path = Path("assets/annotator.png")
        if not avatar_path.exists():
            avatar_path = Path("assets/bob.png")  # legacy fallback
    
    if not avatar_path.exists():
        return None
    
    try:
        with open(avatar_path, "rb") as img_file:
            img_data = img_file.read()
            base64_data = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/png;base64,{base64_data}"
    except Exception as e:
        print(f"Error converting avatar image: {e}")
        return None

def get_annotator_image_data_uri(image_path=None):
    """Alias for get_annotator_image_base64 for consistency"""
    return get_annotator_image_base64(image_path)

# Legacy aliases for backward compatibility
get_bob_image_base64 = get_annotator_image_base64
get_bob_image_data_uri = get_annotator_image_data_uri

if __name__ == "__main__":
    uri = get_annotator_image_base64()
    if uri:
        print("✅ Avatar image successfully converted to base64")
        print(f"📏 Length: {len(uri)} characters")
    else:
        print("❌ Could not convert avatar image")