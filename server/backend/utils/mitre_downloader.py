import os
import sys
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MITREDownloader:
    """Download and process MITRE ATT&CK dataset"""
    
    def __init__(self, data_dir: str = "backend/data"):
        try:
            self.data_dir = Path(data_dir).resolve()
            logger.info(f"Using data directory: {self.data_dir}")
            
            if not self.data_dir.exists():
                logger.info(f"Creating data directory: {self.data_dir}")
                self.data_dir.mkdir(parents=True, exist_ok=True)
            
            self.enterprise_url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
            self.mobile_url = "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json"
            
        except Exception as e:
            logger.error(f"Error initializing MITREDownloader: {e}")
            raise
        
    def download_dataset(self) -> Dict[str, str]:
        """Download MITRE ATT&CK datasets"""
        try:
            logger.info("Starting download of MITRE ATT&CK datasets")
            
            # Download Enterprise ATT&CK
            logger.info(f"Downloading Enterprise ATT&CK from {self.enterprise_url}")
            enterprise_response = requests.get(self.enterprise_url)
            enterprise_response.raise_for_status()
            enterprise_data = enterprise_response.json()
            logger.info("Successfully downloaded Enterprise ATT&CK data")
            
            # Download Mobile ATT&CK
            logger.info(f"Downloading Mobile ATT&CK from {self.mobile_url}")
            mobile_response = requests.get(self.mobile_url)
            mobile_response.raise_for_status()
            mobile_data = mobile_response.json()
            logger.info("Successfully downloaded Mobile ATT&CK data")
            
            # Save datasets
            enterprise_path = self.data_dir / "enterprise-attack.json"
            mobile_path = self.data_dir / "mobile-attack.json"
            
            logger.info(f"Saving Enterprise ATT&CK data to {enterprise_path}")
            with open(enterprise_path, 'w', encoding='utf-8') as f:
                json.dump(enterprise_data, f, indent=2)
            
            logger.info(f"Saving Mobile ATT&CK data to {mobile_path}")
            with open(mobile_path, 'w', encoding='utf-8') as f:
                json.dump(mobile_data, f, indent=2)
            
            logger.info("Successfully saved MITRE ATT&CK datasets")
            
            return {
                "enterprise": str(enterprise_path),
                "mobile": str(mobile_path)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading MITRE ATT&CK datasets: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing MITRE ATT&CK JSON data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading MITRE ATT&CK datasets: {e}")
            raise
    
    def process_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """Process MITRE ATT&CK dataset into training format"""
        try:
            logger.info(f"Processing dataset from {dataset_path}")
            
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            training_examples = []
            technique_count = 0
            
            # Process techniques
            for obj in data.get('objects', []):
                if obj.get('type') == 'attack-pattern':
                    technique_count += 1
                    
                    # Get technique ID
                    technique_id = None
                    for ref in obj.get('external_references', []):
                        if ref.get('source_name') == 'mitre-attack':
                            technique_id = ref.get('external_id')
                            break
                    
                    if not technique_id:
                        logger.warning(f"Skipping technique without ID: {obj.get('name', 'Unknown')}")
                        continue
                    
                    # Create training example
                    example = {
                        "instruction": f"Describe the {obj.get('name')} ({technique_id}) attack technique and how to detect it.",
                        "input": "",
                        "output": self._generate_technique_output(obj, technique_id)
                    }
                    training_examples.append(example)
            
            logger.info(f"Found {technique_count} techniques, processed {len(training_examples)} examples")
            return training_examples
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing dataset JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing dataset: {e}")
            raise
    
    def _generate_technique_output(self, technique: Dict[str, Any], technique_id: str) -> str:
        """Generate detailed output for a technique"""
        try:
            output = []
            
            # Add description
            if 'description' in technique:
                output.append(f"Description: {technique['description']}")
            else:
                logger.warning(f"No description found for technique {technique_id}")
            
            # Add detection strategies
            output.append("\nDetection Strategies:")
            if 'x_mitre_detection' in technique:
                output.append(f"- {technique['x_mitre_detection']}")
            else:
                output.append("- No specific detection strategies provided")
            
            # Add common indicators
            output.append("\nCommon Indicators:")
            if 'x_mitre_platforms' in technique:
                platforms = ", ".join(technique['x_mitre_platforms'])
                output.append(f"- Platforms: {platforms}")
            else:
                output.append("- No platform information available")
            
            # Add mitigation strategies
            output.append("\nMitigation Strategies:")
            if 'x_mitre_data_sources' in technique:
                for source in technique['x_mitre_data_sources']:
                    output.append(f"- Monitor {source}")
            else:
                output.append("- No specific data sources provided")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error generating technique output for {technique_id}: {e}")
            raise

def main():
    """Main function to download and process MITRE ATT&CK datasets"""
    try:
        logger.info("Starting MITRE ATT&CK dataset download and processing")
        
        # Initialize downloader
        downloader = MITREDownloader()
        
        # Download datasets
        logger.info("Downloading datasets...")
        dataset_paths = downloader.download_dataset()
        
        # Process enterprise dataset
        logger.info("Processing Enterprise ATT&CK dataset...")
        enterprise_examples = downloader.process_dataset(dataset_paths['enterprise'])
        
        # Save processed examples
        output_path = Path("backend/data/mitre_training_data.json")
        logger.info(f"Saving processed training data to {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enterprise_examples, f, indent=2)
        
        logger.info(f"Successfully saved {len(enterprise_examples)} training examples")
        logger.info("MITRE ATT&CK dataset processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 