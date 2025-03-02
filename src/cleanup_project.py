#!/usr/bin/env python
"""
Project Cleanup Script
--------------------

Removes unused files and maintains only the essential components
of the streamlined EV processing pipeline.

Essential files:
- main.py
- ev_processor.py
- cleanup_plots.py
"""
import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_project():
    """
    Remove unused files and clean up the project structure.
    Following first principles: keep only what's essential.
    """
    # Files to remove (no longer used in new pipeline)
    unused_files = [
        'visualize_ev.py',
        'process_ev.py',
        'check_data.py',
        'cleanup.py',
        'cleanup_src.py',
        'download_dgt.py'
    ]
    
    # Essential files that should not be deleted
    essential_files = [
        'main.py',
        'ev_processor.py',
        'cleanup_plots.py',
        'cleanup_project.py'  # Keep this script
    ]
    
    src_dir = Path('src')
    
    # Remove unused files
    for file in unused_files:
        file_path = src_dir / file
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"Removed unused file: {file}")
            except Exception as e:
                logger.error(f"Error removing {file}: {str(e)}")
    
    # Remove __pycache__ directory
    pycache_dir = src_dir / '__pycache__'
    if pycache_dir.exists():
        try:
            shutil.rmtree(pycache_dir)
            logger.info("Removed __pycache__ directory")
        except Exception as e:
            logger.error(f"Error removing __pycache__: {str(e)}")
    
    # List remaining files
    logger.info("\nRemaining essential files:")
    for file in src_dir.glob('*.py'):
        if file.name in essential_files:
            logger.info(f"- {file.name}")

def main():
    logger.info("Starting project cleanup")
    cleanup_project()
    logger.info("Project cleanup completed")

if __name__ == "__main__":
    main() 