import asyncio
from typing import List
import GPUtil
import psutil
from loguru import logger
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser

class GPUMonitor:
    """Monitors GPU and system resources for resource management."""
    
    def __init__(self):
        try:
            self.gpus = GPUtil.getGPUs()
        except Exception:
            self.gpus = []
    
    def get_free_memory(self) -> int:
        """Returns free GPU memory in bytes (of the first GPU)."""
        if not self.gpus:
            return 0
        
        # Assume first GPU (can be extended for multi-GPU setup)
        gpu = self.gpus[0]
        return int(gpu.memoryFree * 1024 * 1024)  # Convert to Bytes
    
    def get_memory_utilization(self) -> float:
        """Returns GPU memory utilization as a fraction (0.0 to 1.0)."""
        if not self.gpus:
            return 0.0
        
        gpu = self.gpus[0]
        return gpu.memoryUtil
    
    def is_resource_critical(self, memory_threshold: float = 0.8) -> bool:
        """Checks if resources are below critical level."""
        if not self.gpus:
            return False # Assume CPU is fine for now if no GPU detected
            
        free_memory_pct = self.get_free_memory() / (self.gpus[0].memoryTotal * 1024 * 1024)
        return free_memory_pct < (1 - memory_threshold)

class BatchSemanticSplitter:
    """Resource-efficient semantic splitter with batch processing."""
    
    def __init__(self, 
                 embed_model,
                 buffer_size: int = 1024,
                 similarity_threshold: float = 0.7,
                 batch_size: int = 10,  # Max embeddings per batch
                 gpu_memory_limit: int = 6 * 1024 * 1024 * 1024):  # 6GB in Bytes
        self.embed_model = embed_model
        self.buffer_size = buffer_size
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        self.gpu_memory_limit = gpu_memory_limit
        self._gpu_monitor = GPUMonitor()
        
        # Initialize internal semantic splitter
        self._internal_splitter = SemanticSplitterNodeParser(
            buffer_size=buffer_size,
            breakpoint_percentile_threshold=95, # LlamaIndex default
            embed_model=embed_model
        )
        # Manually override if supported or needed, but SemanticSplitterNodeParser uses BreakpointPercentile or specific threshold logic
        # For simplicity in this integration, we rely on the injected embed_model and basic config.
        # Note: newer LlamaIndex versions might use slightly different init params for threshold. 
        # We will assume standard usage for now.

    async def split_nodes(self, nodes: List[BaseNode]) -> List[BaseNode]:
        """Executes semantic split with resource control."""
        # Check GPU availability before processing
        if self._gpu_monitor.gpus and self._gpu_monitor.get_free_memory() < self.gpu_memory_limit * 0.2:
            logger.warning("Low GPU-RAM availability, switching to fallback strategy")
            return self._fallback_split(nodes)
        
        # For semantic splitting, LlamaIndex needs the full document to make sense of context.
        # Splitting *nodes* (which might already be chunks) semantically is a bit recursive.
        # Usually we pass full documents. 
        # But if we get a list of documents (as nodes), we can process them in batches.
        
        all_split_nodes = []
        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i:i + self.batch_size]
            
            # Check GPU availability before each batch
            if self._gpu_monitor.gpus and self._gpu_monitor.get_free_memory() < self.gpu_memory_limit * 0.3:
                logger.warning(f"GPU-RAM low for batch {i//self.batch_size}, pausing...")
                await asyncio.sleep(1)  # Short pause
            
            # We need to run the splitter. The node parser is typically a sync call in LlamaIndex pipelines,
            # but wrapping it here allows us to control the flow.
            # LlamaIndex parse_nodes expects a list of documents/nodes.
            try:
                # Run in thread to allow async sleep and non-blocking heartbeat
                batch_splits = await asyncio.to_thread(self._internal_splitter.get_nodes_from_documents, batch)
                all_split_nodes.extend(batch_splits)
            except Exception as e:
                logger.error(f"Semantic splitting failed for batch: {e}. Falling back for this batch.")
                all_split_nodes.extend(self._fallback_split(batch))
        
        return all_split_nodes
    
    def _fallback_split(self, nodes: List[BaseNode]) -> List[BaseNode]:
        """Fallback to SentenceSplitter on resource shortage."""
        fallback_splitter = SentenceSplitter(
            chunk_size=self.buffer_size,
            chunk_overlap=int(self.buffer_size * 0.2)
        )
        return fallback_splitter.get_nodes_from_documents(nodes)
