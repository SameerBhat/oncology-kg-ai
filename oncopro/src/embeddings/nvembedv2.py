"""
NVIDIA NV-Embed-v2 embedding model implementation.
"""
from typing import Dict, Any, List, Optional
import torch

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class NVEmbedV2(EmbeddingModel):
    """NVIDIA NV-Embed-v2 embedding model implementation."""
    
    # Model configuration - all in one place!
    MODEL_ID = "nvembedv2"
    MODEL_NAME = "nvidia/NV-Embed-v2"
    MAX_SEQ_LENGTH = 32768
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "model_kwargs": {"device_map": "auto"},
            "tokenizer_kwargs": {"padding_side": "right"},
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        config = self.get_model_config()
        self.model = SentenceTransformer(
            config["model_name"],
            trust_remote_code=config["trust_remote_code"],
            model_kwargs=config["model_kwargs"]
        )
        self.model.max_seq_length = config["max_seq_length"]
        self.model.tokenizer.padding_side = config["tokenizer_kwargs"]["padding_side"]
    
    def add_eos(self, input_examples: List[str]) -> List[str]:
        """Add EOS token to input examples as required by NV-Embed-v2."""
        return [input_example + self.model.tokenizer.eos_token for input_example in input_examples]
    
    def encode_chunks(self, chunks: List[str], **kwargs) -> torch.Tensor:
        """Encode text chunks into embeddings with NV-Embed-v2 specific preprocessing."""
        if self.model is None:
            self.load_with_retry()
        
        # Apply NV-Embed-v2 specific preprocessing
        processed_chunks = self.add_eos(chunks)
        
        # Extract NV-Embed-v2 specific parameters
        use_instruction = kwargs.pop('use_instruction', False)
        task_name = kwargs.pop('task_name', 'example')
        
        # Handle instruction prefix for queries
        if use_instruction:
            task_name_to_instruct = {
                "example": "Given a question, retrieve passages that answer the question",
                "search": "Given a question, retrieve passages that answer the question",
                "qa": "Given a question, retrieve passages that answer the question"
            }
            instruction = task_name_to_instruct.get(task_name, task_name_to_instruct["example"])
            query_prefix = f"Instruct: {instruction}\nQuery: "
            kwargs['prompt'] = query_prefix
        
        # Always normalize embeddings for NV-Embed-v2
        kwargs['normalize_embeddings'] = True
        
        return self.model.encode(
            processed_chunks,
            convert_to_tensor=True,
            **kwargs
        )
    
    def embed_text(self, text: str, use_instruction: bool = False, task_name: str = "example", **kwargs) -> List[float]:
        """
        Embed text by chunking and mean pooling with optional instruction handling.
        
        Args:
            text: Text to embed
            use_instruction: Whether to treat this as a query (add instruction prefix)
            task_name: Task name for instruction generation
            **kwargs: Additional arguments
        """
        # Use a simple chunking approach
        max_words = 6000  # Conservative default
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        embeddings = self.encode_chunks(chunks, use_instruction=use_instruction, task_name=task_name, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding
