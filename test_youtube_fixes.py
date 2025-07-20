#!/usr/bin/env python3
"""
Quick test script to verify YouTube download fixes work.
Run this before deploying to cloud platforms.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.video_processor import VideoProcessor
import time

def test_video_download():
    """Test video download with various strategies."""
    
    # Test URLs - start with simple ones
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (usually works)
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (first YouTube video)
    ]
    
    processor = VideoProcessor("./test_downloads")
    
    print("🧪 Testing YouTube Download Fixes")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📹 Test {i}: {url}")
        print("-" * 30)
        
        try:
            start_time = time.time()
            result = processor.download_audio(url)
            end_time = time.time()
            
            print(f"✅ SUCCESS!")
            print(f"   Title: {result.get('title', 'Unknown')}")
            print(f"   Duration: {result.get('duration', 0)}s")
            print(f"   Audio file: {result.get('audio_path')}")
            print(f"   Download time: {end_time - start_time:.1f}s")
            
            if result.get('subtitle_path'):
                print(f"   Subtitles: {result.get('subtitle_path')}")
                
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            
    print(f"\n🧹 Cleaning up test downloads...")
    
    # Clean up test files
    import shutil
    if os.path.exists("./test_downloads"):
        shutil.rmtree("./test_downloads")
        print("✅ Cleanup complete")

if __name__ == "__main__":
    print("YouTube Download Fix Tester")
    print("This will test the new download strategies locally.")
    print("Make sure you have yt-dlp installed: pip install yt-dlp")
    print()
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Not in virtual environment - consider using one")
    
    print()
    input("Press Enter to start testing...")
    
    test_video_download()
    
    print("\n🎉 Testing complete!")
    print("If tests pass, the fixes should work better on cloud platforms.")
    print("If tests fail, check your internet connection and yt-dlp installation.")
