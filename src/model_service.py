"""Model Service Module for CIPHER Consumer Complaint Intelligence.

Handles local model loading, GPU/CPU device management, tokenizer configuration,
and batch/single complaint inference without retraining or external internet calls.
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CIPHER.ModelService")

# Label mappings
LABEL_DISPLAY_NAMES: Dict[str, str] = {
    "credit_card": "Credit Card",
    "credit_reporting": "Credit Reporting",
    "debt_collection": "Debt Collection",
    "mortgages_and_loans": "Mortgages & Loans",
    "retail_banking": "Retail Banking",
}

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "best-distilbert-complaints"
DEFAULT_MAX_TOKEN_LENGTH = 256

MODEL_NAME = "DistilBERT-base-uncased (fine-tuned)"
MODEL_VERSION = "v1.0"
MODEL_PARAMETER_COUNT = 66_957_317


def _generate_request_id() -> str:
    """Generate a unique CIPHER request reference ID."""
    return f"CIPHER-REQ-{uuid.uuid4().hex[:10].upper()}"


class ModelInferenceError(Exception):
    """Raised when an inference operation encounters an unrecoverable failure."""
    pass


class ModelService:
    """Singleton/Cached inference engine for the fine-tuned DistilBERT complaint classifier."""

    _instance: Optional["ModelService"] = None

    def __init__(self, model_dir: Optional[Union[str, Path]] = None, device_override: Optional[str] = None):
        """Initialize the model service.

        Args:
            model_dir: Path to directory containing saved fine-tuned model artifacts.
            device_override: Optional explicit device string ('cpu' or 'cuda').
        """
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.device_override = device_override

        self.tokenizer = None
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.device = None
        self.is_gpu_active = False
        self.device_name = "Unknown"
        self.max_token_length = DEFAULT_MAX_TOKEN_LENGTH
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.is_loaded = False
        self.load_error: Optional[str] = None
        # Model identity
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION
        self.parameter_count = MODEL_PARAMETER_COUNT

        self._initialize_device()
        self.load_model()

    @classmethod
    def get_instance(cls, model_dir: Optional[Union[str, Path]] = None) -> "ModelService":
        """Retrieve or create the shared singleton instance."""
        if cls._instance is None:
            cls._instance = cls(model_dir=model_dir)
        return cls._instance

    def _initialize_device(self) -> None:
        """Detect and configure the execution device (CUDA vs CPU)."""
        if self.device_override:
            target = self.device_override.lower()
            if target == "cuda" and torch.cuda.is_available():
                self.device = torch.device("cuda")
                self.is_gpu_active = True
                self.device_name = torch.cuda.get_device_name(0)
            else:
                self.device = torch.device("cpu")
                self.is_gpu_active = False
                self.device_name = "CPU"
            return

        if torch.cuda.is_available():
            try:
                # Test basic tensor creation on CUDA to ensure compatibility
                test_tensor = torch.zeros(1).cuda()
                del test_tensor
                self.device = torch.device("cuda")
                self.is_gpu_active = True
                self.device_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU acceleration enabled: {self.device_name}")
            except Exception as e:
                logger.warning(f"CUDA detected but failed test allocation: {e}. Falling back to CPU.")
                self.device = torch.device("cpu")
                self.is_gpu_active = False
                self.device_name = "CPU (Fallback)"
        else:
            self.device = torch.device("cpu")
            self.is_gpu_active = False
            self.device_name = "CPU"
            logger.info("CUDA not available. Using CPU inference.")

    def load_model(self) -> None:
        """Load tokenizer, model weights, and metadata strictly from local files."""
        if not self.model_dir.exists():
            self.load_error = f"Model directory not found at: {self.model_dir}"
            logger.error(self.load_error)
            return

        # Check required files
        expected_files = [
            "config.json",
            "model.safetensors",
            "tokenizer.json",
            "tokenizer_config.json"
        ]
        missing = [f for f in expected_files if not (self.model_dir / f).exists()]
        if missing:
            self.load_error = f"Missing required model files in {self.model_dir}: {missing}"
            logger.error(self.load_error)
            return

        # Load metadata if present
        meta_path = self.model_dir / "model_metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.max_token_length = self.metadata.get("max_token_length", DEFAULT_MAX_TOKEN_LENGTH)
            except Exception as e:
                logger.warning(f"Failed to read model_metadata.json: {e}")

        try:
            # Load tokenizer with local_files_only=True
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_dir),
                local_files_only=True,
            )

            # Load model with local_files_only=True
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_dir),
                local_files_only=True,
            )

            # Extract label mappings from model config
            config_id2label = getattr(self.model.config, "id2label", None)
            if config_id2label:
                self.id2label = {int(k): str(v) for k, v in config_id2label.items()}
            else:
                self.id2label = {
                    0: "credit_card",
                    1: "credit_reporting",
                    2: "debt_collection",
                    3: "mortgages_and_loans",
                    4: "retail_banking",
                }

            config_label2id = getattr(self.model.config, "label2id", None)
            if config_label2id:
                self.label2id = {str(k): int(v) for k, v in config_label2id.items()}
            else:
                self.label2id = {v: k for k, v in self.id2label.items()}

            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            self.load_error = None
            logger.info(f"Model successfully loaded on {self.device_name} from {self.model_dir}")

        except Exception as e:
            self.is_loaded = False
            self.load_error = f"Error during model loading: {str(e)}"
            logger.error(self.load_error, exc_info=True)

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Return diagnostic information about device, model path, and status."""
        return {
            "model_dir": str(self.model_dir),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "parameter_count": self.parameter_count,
            "is_loaded": self.is_loaded,
            "load_error": self.load_error,
            "device": str(self.device),
            "device_name": self.device_name,
            "is_gpu_active": self.is_gpu_active,
            "max_token_length": self.max_token_length,
            "num_classes": len(self.id2label),
            "id2label": self.id2label,
            "test_accuracy": self.metadata.get("test_accuracy", 0.8650),
            "test_weighted_f1": self.metadata.get("test_weighted_f1", 0.8647),
        }

    def predict(self, text: str) -> Dict[str, Any]:
        """Perform classification inference on a single consumer complaint.

        Args:
            text: Complaint text narrative.

        Returns:
            Dictionary containing:
                - success: bool
                - error: Optional error message
                - predicted_category: internal label name
                - display_name: formatted category title
                - top_probability: float in [0.0, 1.0] (uncalibrated)
                - probabilities: dict of label -> probability
                - display_probabilities: dict of display name -> probability
                - latency_ms: float inference duration in milliseconds
                - token_count: number of tokens generated
        """
        if not self.is_loaded:
            return {
                "success": False,
                "error": self.load_error or "Model is not loaded.",
                "predicted_category": None,
                "display_name": None,
                "top_probability": 0.0,
                "probabilities": {},
                "display_probabilities": {},
                "latency_ms": 0.0,
                "token_count": 0,
            }

        # Input validation
        if not isinstance(text, str) or not text.strip():
            return {
                "success": False,
                "error": "Complaint text cannot be empty or whitespace only.",
                "predicted_category": None,
                "display_name": None,
                "top_probability": 0.0,
                "probabilities": {},
                "display_probabilities": {},
                "latency_ms": 0.0,
                "token_count": 0,
            }

        cleaned_text = text.strip()
        start_time = time.perf_counter()

        try:
            inputs = self.tokenizer(
                cleaned_text,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_token_length,
            )

            token_count = int(inputs["input_ids"].shape[1])
            inputs = {key: value.to(self.device) for key, value in inputs.items()}

            with torch.inference_mode():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities_tensor = F.softmax(logits, dim=-1)[0]

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            probs_dict: Dict[str, float] = {}
            display_probs_dict: Dict[str, float] = {}

            for idx in range(len(self.id2label)):
                cat_key = self.id2label[idx]
                p_val = float(probabilities_tensor[idx].item())
                probs_dict[cat_key] = p_val
                disp_name = LABEL_DISPLAY_NAMES.get(cat_key, cat_key.replace("_", " ").title())
                display_probs_dict[disp_name] = p_val

            top_idx = int(torch.argmax(probabilities_tensor).item())
            predicted_cat = self.id2label[top_idx]
            top_prob = float(probabilities_tensor[top_idx].item())
            display_name = LABEL_DISPLAY_NAMES.get(predicted_cat, predicted_cat.replace("_", " ").title())

            req_id = _generate_request_id()
            return {
                "success": True,
                "error": None,
                "request_id": req_id,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "predicted_category": predicted_cat,
                "display_name": display_name,
                "top_probability": top_prob,
                "probabilities": probs_dict,
                "display_probabilities": display_probs_dict,
                "latency_ms": round(elapsed_ms, 2),
                "token_count": token_count,
            }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Inference error during prediction", exc_info=True)
            return {
                "success": False,
                "error": "Inference failed. Please check your input and try again.",
                "request_id": _generate_request_id(),
                "model_name": self.model_name,
                "model_version": self.model_version,
                "predicted_category": None,
                "display_name": None,
                "top_probability": 0.0,
                "probabilities": {},
                "display_probabilities": {},
                "latency_ms": round(elapsed_ms, 2),
                "token_count": 0,
            }

    def predict_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        progress_callback: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform batch inference safely with configurable batch sizing.

        Args:
            texts: List of complaint text strings.
            batch_size: Number of texts per mini-batch.
            progress_callback: Optional callable receiving (current_idx, total_count).

        Returns:
            List of prediction dictionaries corresponding to each input text.
        """
        results: List[Dict[str, Any]] = []
        total_items = len(texts)

        if not self.is_loaded:
            for _ in texts:
                results.append({
                    "success": False,
                    "error": self.load_error or "Model not loaded.",
                    "predicted_category": None,
                    "display_name": None,
                    "top_probability": 0.0,
                    "probabilities": {},
                    "latency_ms": 0.0,
                })
            return results

        for start_idx in range(0, total_items, batch_size):
            end_idx = min(start_idx + batch_size, total_items)
            chunk = texts[start_idx:end_idx]

            # Separate valid and invalid texts in the chunk
            valid_indices: List[int] = []
            valid_texts: List[str] = []

            for offset, text in enumerate(chunk):
                if isinstance(text, str) and text.strip():
                    valid_indices.append(offset)
                    valid_texts.append(text.strip())

            chunk_results: List[Dict[str, Any]] = [None] * len(chunk)  # type: ignore

            # Fill invalid ones immediately
            for offset, text in enumerate(chunk):
                if offset not in valid_indices:
                    chunk_results[offset] = {
                        "success": False,
                        "error": "Empty or invalid complaint text.",
                        "predicted_category": None,
                        "display_name": None,
                        "top_probability": 0.0,
                        "probabilities": {k: 0.0 for k in self.label2id},
                        "latency_ms": 0.0,
                    }

            if valid_texts:
                chunk_start = time.perf_counter()
                try:
                    inputs = self.tokenizer(
                        valid_texts,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=self.max_token_length,
                    )
                    inputs = {key: value.to(self.device) for key, value in inputs.items()}

                    with torch.inference_mode():
                        outputs = self.model(**inputs)
                        probs = F.softmax(outputs.logits, dim=-1)

                    chunk_duration = (time.perf_counter() - chunk_start) * 1000.0
                    avg_latency = chunk_duration / len(valid_texts)

                    for v_pos, orig_offset in enumerate(valid_indices):
                        row_probs = probs[v_pos]
                        top_idx = int(torch.argmax(row_probs).item())
                        cat_key = self.id2label[top_idx]
                        top_val = float(row_probs[top_idx].item())

                        prob_map = {
                            self.id2label[i]: float(row_probs[i].item())
                            for i in range(len(self.id2label))
                        }

                        chunk_results[orig_offset] = {
                            "success": True,
                            "error": None,
                            "predicted_category": cat_key,
                            "display_name": LABEL_DISPLAY_NAMES.get(cat_key, cat_key.replace("_", " ").title()),
                            "top_probability": top_val,
                            "probabilities": prob_map,
                            "latency_ms": round(avg_latency, 2),
                        }

                except Exception as e:
                    logger.error(f"Batch prediction failure on chunk {start_idx}-{end_idx}: {e}")
                    for orig_offset in valid_indices:
                        chunk_results[orig_offset] = {
                            "success": False,
                            "error": f"Batch inference error: {str(e)}",
                            "predicted_category": None,
                            "display_name": None,
                            "top_probability": 0.0,
                            "probabilities": {k: 0.0 for k in self.label2id},
                            "latency_ms": 0.0,
                        }

            results.extend(chunk_results)

            if progress_callback:
                try:
                    progress_callback(end_idx, total_items)
                except Exception:
                    pass

        return results
