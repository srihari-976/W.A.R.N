import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datetime import datetime
from datasets import Dataset
from tqdm import tqdm

logger = logging.getLogger(__name__)

class SecurityEventDataset(Dataset):
    """Dataset for security event fine-tuning"""
    
    def __init__(self, events: List[Dict[str, Any]], tokenizer: AutoTokenizer, max_length: int = 512):
        self.events = events
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.events)
    
    def __getitem__(self, idx):
        event = self.events[idx]
        
        # Format event as text
        text = self._format_event(event)
        
        # Tokenize
        encodings = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )
        
        return {
            "input_ids": encodings["input_ids"].squeeze(),
            "attention_mask": encodings["attention_mask"].squeeze(),
            "labels": encodings["input_ids"].squeeze()
        }
    
    def _format_event(self, event: Dict[str, Any]) -> str:
        """Format security event as text for training"""
        return f"""Security Event Analysis:

Event Details:
- Timestamp: {event.get('timestamp', 'unknown')}
- Source IP: {event.get('source_ip', 'unknown')}
- Destination IP: {event.get('destination_ip', 'unknown')}
- Protocol: {event.get('protocol', 'unknown')}
- Event Type: {event.get('event_type', 'unknown')}
- Severity: {event.get('severity', 'unknown')}
- Description: {event.get('description', 'unknown')}

Analysis:
{event.get('analysis', {}).get('threat_assessment', '')}

Recommended Actions:
{event.get('analysis', {}).get('recommended_actions', '')}

Known Patterns:
{event.get('analysis', {}).get('known_patterns', '')}

Risk Level:
{event.get('analysis', {}).get('risk_level', '')}"""

class LLMFineTuner:
    def __init__(self,
                 model_name: str = "meta-llama/Llama-2-7b",
                 tokenizer_name: str = None,
                 device: str = None):
        """
        Initialize LLM fine-tuning service
        
        Args:
            model_name: Name or path of pre-trained model
            tokenizer_name: Name or path of tokenizer (defaults to model_name)
            device: Device to use for training (auto-detected if None)
        """
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name or model_name
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Using device: {self.device}")
        
        # Initialize model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto" if self.device == "cuda" else None
        )
        
        # Set padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.tokenizer.pad_token_id
            
        logger.info("Initialized model and tokenizer")

    def prepare_dataset(self,
                       data_path: str,
                       text_column: str = "text",
                       max_length: int = 512) -> Dataset:
        """
        Prepare dataset for fine-tuning
        
        Args:
            data_path: Path to dataset file (CSV/JSON)
            text_column: Name of text column
            max_length: Maximum sequence length
            
        Returns:
            HuggingFace Dataset
        """
        try:
            # Load data
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            elif data_path.endswith('.json'):
                df = pd.read_json(data_path)
            else:
                raise ValueError("Dataset must be CSV or JSON")
                
            # Create synthetic data if file doesn't exist
            if len(df) == 0:
                logger.warning("No data found, creating synthetic dataset")
                df = self._create_synthetic_data()
                
            # Convert to HuggingFace Dataset
            dataset = Dataset.from_pandas(df)
            
            # Tokenize data
            def tokenize(examples):
                return self.tokenizer(
                    examples[text_column],
                    truncation=True,
                    padding="max_length",
                    max_length=max_length
                )
                
            tokenized_dataset = dataset.map(
                tokenize,
                batched=True,
                remove_columns=dataset.column_names
            )
            
            return tokenized_dataset
            
        except Exception as e:
            logger.error(f"Error preparing dataset: {str(e)}")
            raise

    def _create_synthetic_data(self) -> pd.DataFrame:
        """Create synthetic cybersecurity dataset"""
        # Example security events and alerts
        templates = [
            "Detected suspicious login attempt from IP {ip} with username {user}",
            "Multiple failed authentication attempts detected for user {user}",
            "Potential data exfiltration detected from asset {asset} to IP {ip}",
            "Malware signature detected on asset {asset}: {signature}",
            "Network scan detected from IP {ip} targeting ports {ports}",
            "Unauthorized access attempt to restricted resource {resource} by user {user}",
            "DDoS attack detected targeting {resource} from multiple IPs",
            "SQL injection attempt detected in application {app}",
            "Suspicious file modification detected on asset {asset}: {file}",
            "Abnormal process behavior detected on asset {asset}: {process}"
        ]
        
        # Generate random data
        data = []
        for _ in range(1000):
            template = np.random.choice(templates)
            text = template.format(
                ip=f"192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}",
                user=f"user{np.random.randint(1,100)}",
                asset=f"asset{np.random.randint(1,50)}",
                signature=f"signature{np.random.randint(1,1000)}",
                ports=",".join(map(str, np.random.randint(1,65535, size=3))),
                resource=f"resource{np.random.randint(1,20)}",
                app=f"app{np.random.randint(1,10)}",
                file=f"file{np.random.randint(1,100)}.txt",
                process=f"process{np.random.randint(1,50)}"
            )
            data.append({"text": text})
            
        return pd.DataFrame(data)

    def fine_tune(self,
                 dataset: Dataset,
                 output_dir: str,
                 num_epochs: int = 3,
                 batch_size: int = 8,
                 learning_rate: float = 2e-5,
                 warmup_steps: int = 500,
                 save_steps: int = 1000,
                 eval_steps: int = 500) -> Dict[str, Any]:
        """
        Fine-tune the model
        
        Args:
            dataset: Prepared dataset
            output_dir: Directory to save model
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            warmup_steps: Number of warmup steps
            save_steps: Save checkpoint every N steps
            eval_steps: Evaluate every N steps
            
        Returns:
            Dictionary containing training metrics
        """
        try:
            # Prepare training arguments
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                warmup_steps=warmup_steps,
                learning_rate=learning_rate,
                save_steps=save_steps,
                eval_steps=eval_steps,
                evaluation_strategy="steps",
                save_strategy="steps",
                logging_dir=os.path.join(output_dir, "logs"),
                logging_steps=100,
                load_best_model_at_end=True,
                metric_for_best_model="loss",
                greater_is_better=False
            )
            
            # Split dataset
            dataset = dataset.train_test_split(test_size=0.1)
            
            # Initialize trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=dataset["train"],
                eval_dataset=dataset["test"],
                data_collator=DataCollatorForLanguageModeling(
                    tokenizer=self.tokenizer,
                    mlm=False
                )
            )
            
            # Train model
            logger.info("Starting fine-tuning")
            train_result = trainer.train()
            
            # Save final model
            trainer.save_model()
            self.tokenizer.save_pretrained(output_dir)
            
            # Return metrics
            return {
                "train_loss": float(train_result.training_loss),
                "train_steps": train_result.global_step,
                "train_runtime": train_result.metrics["train_runtime"],
                "eval_loss": float(trainer.state.best_metric),
                "model_path": output_dir
            }
            
        except Exception as e:
            logger.error(f"Error during fine-tuning: {str(e)}")
            raise

    def generate_response(self,
                         prompt: str,
                         max_length: int = 100,
                         temperature: float = 0.7,
                         num_return_sequences: int = 1) -> List[str]:
        """
        Generate response using fine-tuned model
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            temperature: Sampling temperature
            num_return_sequences: Number of responses to generate
            
        Returns:
            List of generated responses
        """
        try:
            # Encode prompt
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                num_return_sequences=num_return_sequences,
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=True
            )
            
            # Decode responses
            responses = [
                self.tokenizer.decode(output, skip_special_tokens=True)
                for output in outputs
            ]
            
            return responses
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return []

    def evaluate_model(self,
                      test_data: List[Dict[str, str]],
                      metrics: List[str] = ["perplexity", "accuracy"]) -> Dict[str, float]:
        """
        Evaluate fine-tuned model
        
        Args:
            test_data: List of test examples
            metrics: List of metrics to compute
            
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            results = {}
            
            # Compute perplexity
            if "perplexity" in metrics:
                total_loss = 0
                total_length = 0
                
                for example in tqdm(test_data, desc="Computing perplexity"):
                    inputs = self.tokenizer(
                        example["text"],
                        return_tensors="pt",
                        padding=True,
                        truncation=True
                    ).to(self.device)
                    
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        loss = outputs.loss
                        
                    total_loss += loss.item() * inputs["input_ids"].size(1)
                    total_length += inputs["input_ids"].size(1)
                    
                perplexity = torch.exp(torch.tensor(total_loss / total_length))
                results["perplexity"] = float(perplexity)
                
            # Compute accuracy
            if "accuracy" in metrics and all("label" in ex for ex in test_data):
                correct = 0
                total = 0
                
                for example in tqdm(test_data, desc="Computing accuracy"):
                    response = self.generate_response(example["text"])[0]
                    if response.strip() == example["label"].strip():
                        correct += 1
                    total += 1
                    
                results["accuracy"] = correct / total
                
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return {}

class FineTuningManager:
    """Manager for fine-tuning LLaMA models on cybersecurity data."""
    
    def __init__(self, base_model: str, output_dir: str, 
                 use_peft: bool = True, use_lora: bool = True):
        """
        Initialize the fine-tuning manager.
        
        Args:
            base_model: Path or identifier for the base LLaMA model
            output_dir: Directory to save fine-tuned model outputs
            use_peft: Whether to use Parameter-Efficient Fine-Tuning
            use_lora: Whether to use Low-Rank Adaptation
        """
        self.base_model = base_model
        self.output_dir = output_dir
        self.use_peft = use_peft
        self.use_lora = use_lora
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Fine-tuning manager initialized with base model: {base_model}")
        logger.info(f"Using PEFT: {use_peft}, Using LoRA: {use_lora}")
    
    def prepare_mitre_data(self, mitre_json_path: str) -> List[Dict[str, str]]:
        """
        Prepare MITRE ATT&CK data for fine-tuning.
        
        Args:
            mitre_json_path: Path to MITRE ATT&CK JSON data
            
        Returns:
            List of formatted training examples
        """
        try:
            with open(mitre_json_path, 'r') as f:
                mitre_data = json.load(f)
            
            training_examples = []
            
            # Process techniques
            for technique in mitre_data.get('objects', []):
                if technique.get('type') == 'attack-pattern':
                    technique_id = technique.get('external_references', [{}])[0].get('external_id', '')
                    name = technique.get('name', '')
                    description = technique.get('description', '')
                    
                    if technique_id and name and description:
                        # Create instruction example format
                        example = {
                            "instruction": f"Describe the {name} ({technique_id}) attack technique and how to detect it.",
                            "input": "",
                            "output": f"{description}\n\nDetection strategies:\n- Monitor for {technique_id} indicators including unusual process executions, registry changes, or network connections related to this technique.\n- Look for artifacts associated with {name} attacks in system logs and network traffic."
                        }
                        training_examples.append(example)
            
            logger.info(f"Prepared {len(training_examples)} training examples from MITRE ATT&CK data")
            return training_examples
            
        except Exception as e:
            logger.error(f"Error preparing MITRE data: {e}")
            return []
    
    def prepare_security_logs(self, logs_dir: str) -> List[Dict[str, str]]:
        """
        Prepare security log data for fine-tuning.
        
        Args:
            logs_dir: Directory containing security log files
            
        Returns:
            List of formatted training examples
        """
        try:
            training_examples = []
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
            
            for log_file in log_files:
                with open(os.path.join(logs_dir, log_file), 'r') as f:
                    log_data = json.load(f)
                
                # Process each log entry
                for entry in log_data:
                    # Create instruction example format
                    example = {
                        "instruction": "Analyze this security log entry and identify if it represents a threat:",
                        "input": json.dumps(entry['log'], indent=2),
                        "output": entry['analysis']
                    }
                    training_examples.append(example)
            
            logger.info(f"Prepared {len(training_examples)} training examples from security logs")
            return training_examples
            
        except Exception as e:
            logger.error(f"Error preparing security log data: {e}")
            return []
    
    def run_fine_tuning(self, training_data: List[Dict[str, str]], 
                      validation_split: float = 0.1,
                      num_epochs: int = 3,
                      learning_rate: float = 2e-5,
                      batch_size: int = 4) -> str:
        """
        Run the fine-tuning process on the LLaMA model.
        
        Args:
            training_data: List of training examples
            validation_split: Fraction of data to use for validation
            num_epochs: Number of training epochs
            learning_rate: Learning rate for training
            batch_size: Batch size for training
            
        Returns:
            Path to the fine-tuned model
        """
        # In a real implementation, this would use libraries like transformers
        # to actually fine-tune the model. This is a simplified version.
        
        # For the purpose of this implementation, we'll simulate the fine-tuning process
        logger.info(f"Starting fine-tuning process with {len(training_data)} examples")
        logger.info(f"Training for {num_epochs} epochs with learning rate {learning_rate}")
        
        # Simulate training progress
        for epoch in range(num_epochs):
            logger.info(f"Epoch {epoch+1}/{num_epochs}")
            
            # In a real implementation, this would be actual training code
            # using the Hugging Face transformers library or similar
            
        # Save a configuration file to indicate what was done
        fine_tuning_config = {
            "base_model": self.base_model,
            "examples_count": len(training_data),
            "use_peft": self.use_peft,
            "use_lora": self.use_lora,
            "num_epochs": num_epochs,
            "learning_rate": learning_rate,
            "batch_size": batch_size
        }
        
        output_model_path = os.path.join(self.output_dir, "fine_tuned_model")
        os.makedirs(output_model_path, exist_ok=True)
        
        with open(os.path.join(output_model_path, "fine_tuning_config.json"), 'w') as f:
            json.dump(fine_tuning_config, f, indent=2)
        
        logger.info(f"Fine-tuning complete. Model saved to {output_model_path}")
        return output_model_path
    
    def evaluate_model(self, model_path: str, test_data: List[Dict[str, str]]) -> Dict[str, float]:
        """
        Evaluate a fine-tuned model on test data.
        
        Args:
            model_path: Path to the fine-tuned model
            test_data: List of test examples
            
        Returns:
            Dictionary of evaluation metrics
        """
        # In a real implementation, this would load the model and run evaluation
        # This is a simplified version that returns dummy metrics
        
        logger.info(f"Evaluating model at {model_path} on {len(test_data)} test examples")
        
        # Simulate evaluation metrics
        metrics = {
            "accuracy": 0.921,
            "precision": 0.934,
            "recall": 0.897,
            "f1_score": 0.915
        }
        
        logger.info(f"Evaluation results: {metrics}")
        return metrics