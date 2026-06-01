import os
from downloader import Downloader
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def main():
    # Folder with difficult characters
    folder_name = "Mỗi Ngày Một Chút short"
    # A video from that channel (taken from history or a known one, e.g. the one that worked or failed)
    # Let's try downloading the one that exists to see if it skips (normal) or fails
    # flPHEu-MJ_jQ is the one that exists. 
    # Let's try a DIFFERENT one if possible, or just re-download this one to verify permissions/path.
    video_url = "https://www.youtube.com/shorts/lPHEu-MJ_jQ" 

    print(f"Testing download into: {folder_name}")
    
    downloader = Downloader()
    try:
        success = downloader.download_video(video_url, subfolder=folder_name)
        if success:
            print("Download SUCCESS")
        else:
            print("Download FAILED (indicated by return value)")
    except Exception as e:
        print(f"Download CRASHED: {e}")

if __name__ == "__main__":
    main()
