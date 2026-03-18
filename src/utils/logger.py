import logging
import os

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'pipeline.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
