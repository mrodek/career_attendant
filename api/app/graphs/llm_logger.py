"""
Custom callback handler for logging LLM interactions.

Logs all prompts and responses without needing LangSmith.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger("api.llm")


class LLMLoggingHandler(BaseCallbackHandler):
    """Callback handler that logs all LLM interactions."""
    
    def __init__(self, log_prompts: bool = True, log_responses: bool = True):
        self.log_prompts = log_prompts
        self.log_responses = log_responses
        self._current_run: Dict[str, Any] = {}
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log when LLM starts processing."""
        self._current_run[str(run_id)] = {
            "start_time": datetime.now().isoformat(),
            "model": serialized.get("kwargs", {}).get("model_name", "unknown"),
        }
        
        if self.log_prompts:
            logger.info(f"🤖 LLM Start | run_id={run_id}")
            logger.info(f"   Model: {serialized.get('kwargs', {}).get('model_name', 'unknown')}")
            for i, prompt in enumerate(prompts):
                # Truncate very long prompts in logs
                prompt_preview = prompt[:2000] + "..." if len(prompt) > 2000 else prompt
                logger.info(f"   Prompt[{i}]: {prompt_preview}")
    
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log when chat model starts (for ChatOpenAI)."""
        model_name = serialized.get("kwargs", {}).get("model_name", "unknown")
        self._current_run[str(run_id)] = {
            "start_time": datetime.now().isoformat(),
            "model": model_name,
        }
        
        if self.log_prompts:
            logger.info(f"🤖 Chat LLM Start | run_id={run_id} | model={model_name}")
            for batch_idx, message_batch in enumerate(messages):
                for msg in message_batch:
                    role = msg.type  # 'system', 'human', 'ai'
                    content = msg.content
                    # Truncate very long messages
                    content_preview = content[:2000] + "..." if len(content) > 2000 else content
                    logger.info(f"   [{role.upper()}]: {content_preview}")
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM response."""
        run_info = self._current_run.pop(str(run_id), {})
        
        if self.log_responses:
            logger.info(f"✅ LLM End | run_id={run_id}")
            
            # Log token usage if available
            if response.llm_output:
                usage = response.llm_output.get("token_usage", {})
                if usage:
                    logger.info(f"   Tokens: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}, total={usage.get('total_tokens')}")
            
            # Log the response content
            for gen_idx, generations in enumerate(response.generations):
                for gen in generations:
                    content = gen.text if hasattr(gen, 'text') else str(gen)
                    # Truncate very long responses
                    content_preview = content[:3000] + "..." if len(content) > 3000 else content
                    logger.info(f"   Response: {content_preview}")
    
    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM errors."""
        self._current_run.pop(str(run_id), None)
        logger.error(f"❌ LLM Error | run_id={run_id} | error={str(error)}")


# Singleton instance for easy access
llm_logging_handler = LLMLoggingHandler()


def get_llm_callbacks() -> List[BaseCallbackHandler]:
    """Get the list of callbacks to use with LLM calls."""
    return [llm_logging_handler]
