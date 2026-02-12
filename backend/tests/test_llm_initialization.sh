#!/bin/bash
# Test script for GitHub Issue #3 - LLM Initialization Fix
# 
# This script runs inside the Docker container where all dependencies are available.
# Usage: docker compose exec backend /app/tests/test_llm_initialization.sh

set -e

echo ""
echo "============================================================"
echo "   LLM Initialization Test Suite (GitHub Issue #3)"
echo "============================================================"
echo ""
echo "This test verifies that the indentation bug has been fixed"
echo "and LLM instances are created correctly."
echo ""

# Test 1: Ollama Provider (use_hot_reload=False)
echo "============================================================"
echo "TEST 1: Ollama Provider (use_hot_reload=False)"
echo "============================================================"
python3 -c "
import sys
sys.path.insert(0, '/app/src')

from core.config import create_llm_instances, LLMConfig

config = LLMConfig(
    provider='ollama',
    model='llama3:latest',
    api_key=None,
    embedding_provider='ollama',
    embedding_model='nomic-embed-text',
    chroma_path='./chroma_data',
    collection_name='test',
    project_collection_name='test_project',
    base_url=None
)

instances = create_llm_instances(config, use_hot_reload=False)

assert instances.get('llm') is not None, '❌ LLM instance is None!'
assert instances.get('embeddings') is not None, '❌ Embeddings instance is None!'

print(f'✅ LLM instance created: {type(instances[\"llm\"]).__name__}')
print(f'✅ Embeddings instance created: {type(instances[\"embeddings\"]).__name__}')
print('✅ TEST 1 PASSED')
"

echo ""

# Test 2: Hot-Reload Path
echo "============================================================"
echo "TEST 2: Hot-Reload Path (use_hot_reload=True)"
echo "============================================================"
python3 -c "
import sys
sys.path.insert(0, '/app/src')

from core.config import create_llm_instances, LLMConfig

config = LLMConfig(
    provider='ollama',
    model='llama3:latest',
    api_key=None,
    embedding_provider='ollama',
    embedding_model='nomic-embed-text',
    chroma_path='./chroma_data',
    collection_name='test',
    project_collection_name='test_project',
    base_url=None
)

instances = create_llm_instances(config, use_hot_reload=True)

assert instances.get('llm') is not None, '❌ LLM instance is None with hot_reload=True!'
assert instances.get('embeddings') is not None, '❌ Embeddings instance is None with hot_reload=True!'

print(f'✅ LLM instance created: {type(instances[\"llm\"]).__name__}')
print(f'✅ Embeddings instance created: {type(instances[\"embeddings\"]).__name__}')
print('✅ TEST 2 PASSED')
"

echo ""
echo "============================================================"
echo "TEST SUMMARY"
echo "============================================================"
echo "✅ PASSED: Ollama Provider (use_hot_reload=False)"
echo "✅ PASSED: Hot-Reload Path (use_hot_reload=True)"
echo ""
echo "Total: 2/2 tests passed"
echo ""
echo "🎉 All tests passed! The fix is working correctly."
echo ""
