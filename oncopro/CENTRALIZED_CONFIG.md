# Centralized Embedding Model Configuration

## Overview

This document describes the refactored embedding model architecture that centralizes all model-specific configuration within the model classes themselves, following the DRY principle and improving maintainability.

## Problems with the Previous Approach

### Before (Scattered Configuration)
```
┌─ settings.py ─────────────────┐
│ JINA4_MODEL_NAME = "..."      │
│ JINA4_MAX_SEQ_LENGTH = 8192   │
│ QWEN3_MODEL_NAME = "..."      │
│ QWEN3_MAX_SEQ_LENGTH = 32768  │
└───────────────────────────────┘
           ↓ imports
┌─ jina4.py ───────────────────┐
│ from ..config import         │
│   JINA4_MODEL_NAME,          │
│   JINA4_MAX_SEQ_LENGTH       │
└──────────────────────────────┘
           ↓ registers
┌─ factory.py ─────────────────┐
│ _models = {                  │
│   "jina4": Jina4Embedding,   │
│   "qwen3": Qwen3Embedding,   │
│ }                            │
└──────────────────────────────┘
```

**Issues:**
- Configuration scattered across multiple files
- Need to update 3+ files when adding a new model
- Tight coupling between settings and implementations
- Violates DRY principle
- Poor maintainability

## New Approach (Centralized Configuration)

### After (Self-Contained Models)
```
┌─ jina4.py ──────────────────────────┐
│ class Jina4Embedding(EmbeddingModel): │
│   MODEL_ID = "jina4"                 │
│   MODEL_NAME = "jinaai/..."          │
│   MAX_SEQ_LENGTH = 8192              │
│                                      │
│   def get_model_config(self): ...    │
│   def load_model(self): ...          │
└──────────────────────────────────────┘
           ↓ auto-discovery
┌─ factory.py ─────────────────────────┐
│ _model_classes = [                   │
│   Jina4Embedding,                    │
│   Qwen3Embedding,                    │
│   OpenAIEmbedding,                   │
│ ]                                    │
│                                      │
│ def _get_models_registry(cls):       │
│   return {model_cls.MODEL_ID:        │
│           model_cls for model_cls    │
│           in cls._model_classes}     │
└──────────────────────────────────────┘
```

## Key Benefits

### 1. **Single Source of Truth**
Each model class contains all its configuration:
```python
class NewModelEmbedding(EmbeddingModel):
    MODEL_ID = "new_model"
    MODEL_NAME = "company/new-model-v1"
    MAX_SEQ_LENGTH = 4096
    
    # Implementation follows...
```

### 2. **Easy to Add New Models**
To add a new model, you only need to:

1. Create the model class
2. Define the three required constants
3. Implement the required methods
4. Add to the factory's `_model_classes` list

That's it! No need to update multiple files.

### 3. **Auto-Discovery**
The factory automatically builds the registry from available classes:
```python
def _get_models_registry(cls) -> Dict[str, Type[EmbeddingModel]]:
    return {model_cls.MODEL_ID: model_cls for model_cls in cls._model_classes}
```

### 4. **Runtime Model Information**
Get model info without instantiating:
```python
info = EmbeddingModelFactory.get_model_info("jina4")
# Returns: {"id": "jina4", "name": "jinaai/...", "max_seq_length": "8192"}
```

## File Structure Changes

### Removed from `settings.py`
```python
# These are now in individual model classes
JINA4_MODEL_NAME = "jinaai/jina-embeddings-v4"
JINA4_MAX_SEQ_LENGTH = 8192
QWEN3_MODEL_NAME = "Qwen/Qwen3-Embedding-4B" 
QWEN3_MAX_SEQ_LENGTH = 32768
OPENAI_MODEL_NAME = "text-embedding-3-small"
OPENAI_MAX_SEQ_LENGTH = 8192
```

### Updated Base Class
```python
class EmbeddingModel(ABC):
    # Class-level configuration - override in subclasses
    MODEL_NAME: str = None
    MAX_SEQ_LENGTH: int = None  
    MODEL_ID: str = None
    
    def __init__(self, ...):
        # Validates that subclass defines required configuration
        if self.MODEL_NAME is None or self.MAX_SEQ_LENGTH is None or self.MODEL_ID is None:
            raise ValueError(f"{self.__class__.__name__} must define MODEL_NAME, MAX_SEQ_LENGTH, and MODEL_ID")
```

### Enhanced Factory
```python
class EmbeddingModelFactory:
    _model_classes = [Jina4Embedding, Qwen3Embedding, OpenAIEmbedding]
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, str]:
        """Get information about a specific model."""
        models = cls._get_models_registry()
        model_cls = models[model_name]
        return {
            "id": model_cls.MODEL_ID,
            "name": model_cls.MODEL_NAME, 
            "max_seq_length": str(model_cls.MAX_SEQ_LENGTH)
        }
```

## Migration Guide

### For Existing Code
- No changes needed for code that uses `EmbeddingModelFactory.create_model()`
- Model instances still work the same way
- Configuration is just accessed differently internally

### For Adding New Models
Instead of:
1. ❌ Add constants to `settings.py`
2. ❌ Import constants in model class
3. ❌ Register in factory manually
4. ❌ Update documentation

Now just:
1. ✅ Create model class with configuration constants
2. ✅ Add to factory's `_model_classes` list

## Example: Adding a New Model

```python
# That's all you need!
class BGEEmbedding(EmbeddingModel):
    MODEL_ID = "bge"
    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    MAX_SEQ_LENGTH = 512
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        # Implementation...
        pass
```

## Environment Configuration

The `.env` file still controls which model to use:
```bash
# Available models are now defined in their respective classes
EMBEDDING_MODEL=qwen3
```

The `settings.py` gets the model name from environment and the factory handles the rest.

## Conclusion

This refactoring achieves:
- ✅ **Centralized configuration**: All model config in model classes
- ✅ **DRY principle**: No duplication across files
- ✅ **Easy extensibility**: Add models by creating one class
- ✅ **Better maintainability**: Single place to update model details
- ✅ **Backward compatibility**: Existing code continues to work
- ✅ **Self-documenting**: Model capabilities are clear from the class

The architecture is now much cleaner and follows object-oriented principles where data and behavior are encapsulated together.
