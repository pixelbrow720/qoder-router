from fastapi import APIRouter
from app.services.model_catalog import public_model_catalog


def _slug(nama: str) -> str:
    """Model ID yang mudah dibaca: 'Kimi-K3.1-Pro' -> 'kimi-k3.1-pro'."""
    return nama.lower().replace(" ", "-").replace("_", "-")


router = APIRouter(tags=["models"])


@router.get("/v1/models")
async def list_models():
    models = [m for m in public_model_catalog() if m.get("kind") == "model"]
    data = [
        {
                "id": _slug(model["name"]),  # ID ramah: kimi-k3.1-pro, qwen3.8-flash, dst
                "object": "model",
                # Anthropic clients read `type` + `display_name`; OpenAI
                # clients ignore the extra fields, so one list serves both.
                "type": "model",
                "created": 1700000000,
                "created_at": "2023-11-14T00:00:00Z",
                "owned_by": "qoder",
                "display_name": model["name"],
                "credit_factor": model["credit_factor"],
                "context_length": model["context_length"],
                "context_windows": model["context_windows"],
                "max_input_tokens": model["max_input_tokens"],
                "is_reasoning": model["is_reasoning"],
                "is_vision": model["is_vision"],
            }
            for model in models
    ]
    return {
        "object": "list",
        "data": data,
        "has_more": False,
        "first_id": data[0]["id"] if data else None,
        "last_id": data[-1]["id"] if data else None,
    }


@router.get("/api/models/catalog")
async def model_catalog():
    return public_model_catalog()
