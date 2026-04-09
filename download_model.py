import os
from huggingface_hub import snapshot_download
from pathlib import Path

# Configuration
MODEL_REPO = "Qwen/Qwen3-VL-32B-Instruct-FP8"
# Download to the 'models' subdirectory within the current directory
LOCAL_DIR = Path("models/Qwen3-VL-32B-Instruct-FP8").resolve()

def download_model():
    print(f"Starting download of {MODEL_REPO}...")
    print(f"Target directory: {LOCAL_DIR}")
    
    # Create directory if it doesn't exist
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # snapshot_download automatically handles resume (resume_download=True is default in newer versions, 
        # but we can omit or explicit it if needed. 'local_dir' parameter downloads to specific folder)
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=LOCAL_DIR,
            resume_download=True,
            max_workers=8  # Adjust based on network/CPU
        )
        print("\nDownload completed successfully!")
        print(f"Model saved to: {LOCAL_DIR}")
        
    except Exception as e:
        print(f"\nDownload failed with error: {e}")
        print("You can run this script again to resume the download.")

if __name__ == "__main__":
    download_model()
