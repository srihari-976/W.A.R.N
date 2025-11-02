import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from .fine_tuning import LLMFineTuner

logger = logging.getLogger(__name__)

class MITREIntegration:
    """Integrate MITRE ATT&CK data with LLM fine-tuning"""
    
    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = Path(data_dir)
        self.training_data_path = self.data_dir / "mitre_training_data.json"
        self.fine_tuner = LLMFineTuner()
    
    def load_training_data(self) -> List[Dict[str, str]]:
        """Load processed MITRE ATT&CK training data"""
        try:
            if not self.training_data_path.exists():
                raise FileNotFoundError(f"Training data not found at {self.training_data_path}")
            
            with open(self.training_data_path, 'r') as f:
                training_data = json.load(f)
            
            logger.info(f"Loaded {len(training_data)} training examples")
            return training_data
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            raise
    
    def fine_tune_with_mitre(self, output_dir: str = "backend/models/llm"):
        """Fine-tune LLM with MITRE ATT&CK data"""
        try:
            # Load training data
            training_data = self.load_training_data()
            
            # Prepare dataset
            dataset = self.fine_tuner.prepare_dataset(
                data_path=str(self.training_data_path),
                text_column="instruction"
            )
            
            # Fine-tune model
            metrics = self.fine_tuner.fine_tune(
                dataset=dataset,
                output_dir=output_dir,
                num_epochs=3,
                batch_size=4,
                learning_rate=2e-5
            )
            
            logger.info(f"Fine-tuning completed with metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error fine-tuning with MITRE data: {e}")
            raise
    
    def evaluate_mitre_knowledge(self, test_examples: List[Dict[str, str]]) -> Dict[str, float]:
        """Evaluate model's knowledge of MITRE ATT&CK techniques"""
        try:
            results = self.fine_tuner.evaluate_model(
                test_data=test_examples,
                metrics=["accuracy", "perplexity"]
            )
            
            logger.info(f"Evaluation results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating MITRE knowledge: {e}")
            raise

def main():
    """Main function to run MITRE integration"""
    try:
        # Initialize integration
        integration = MITREIntegration()
        
        # Fine-tune model
        metrics = integration.fine_tune_with_mitre()
        
        # Create test examples
        test_examples = [
            {
                "instruction": "Describe the T1059 (Command and Scripting Interpreter) attack technique.",
                "input": "",
                "output": "Command and Scripting Interpreter (T1059) is a technique where adversaries use command and script interpreters to execute commands, scripts, or binaries."
            },
            {
                "instruction": "How can we detect T1566 (Phishing) attacks?",
                "input": "",
                "output": "Phishing (T1566) can be detected by monitoring for suspicious emails, analyzing email headers, and tracking user interactions with suspicious links."
            }
        ]
        
        # Evaluate model
        evaluation = integration.evaluate_mitre_knowledge(test_examples)
        
        logger.info("MITRE integration completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main() 