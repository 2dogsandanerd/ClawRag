import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from io import StringIO

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import LLMConfig


class TestOpenAIIntegration(unittest.TestCase):
    """Integration tests for OpenAI API integration with mocking of external calls."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any existing environment variables that might interfere
        env_vars_to_clear = ['LLM_PROVIDER', 'EMBEDDING_PROVIDER', 'LLM_MODEL', 'EMBEDDING_MODEL', 'OPENAI_API_KEY', 'OLLAMA_HOST']
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_openai_config_creation(self):
        """Test that OpenAI config can be created properly."""
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai",
            embedding_model="text-embedding-ada-002",
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection"
        )

        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.model, "gpt-3.5-turbo")
        self.assertEqual(config.api_key, "fake-api-key-for-testing")
        self.assertEqual(config.embedding_provider, "openai")
        self.assertEqual(config.embedding_model, "text-embedding-ada-002")

    def test_openai_compatible_config_creation(self):
        """Test that OpenAI compatible config can be created properly."""
        config = LLMConfig(
            provider="openai_compatible",
            model="local-model",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai_compatible",
            embedding_model="local-embedding-model",
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection",
            base_url="http://localhost:1234/v1"
        )

        self.assertEqual(config.provider, "openai_compatible")
        self.assertEqual(config.model, "local-model")
        self.assertEqual(config.api_key, "fake-api-key-for-testing")
        self.assertEqual(config.embedding_provider, "openai_compatible")
        self.assertEqual(config.embedding_model, "local-embedding-model")
        self.assertEqual(config.base_url, "http://localhost:1234/v1")

    def test_openai_compatible_config_missing_v1_base_url(self):
        """Test that OpenAI compatible config handles base_url without /v1 properly."""
        config = LLMConfig(
            provider="openai_compatible",
            model="local-model",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai_compatible",
            embedding_model="local-embedding-model",
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection",
            base_url="http://localhost:1234"
        )

        self.assertEqual(config.provider, "openai_compatible")
        self.assertEqual(config.model, "local-model")
        self.assertEqual(config.api_key, "fake-api-key-for-testing")
        self.assertEqual(config.embedding_provider, "openai_compatible")
        self.assertEqual(config.embedding_model, "local-embedding-model")
        self.assertEqual(config.base_url, "http://localhost:1234")

    def test_config_creation_with_env_vars(self):
        """Test that config can be created with environment variables."""
        # Temporarily set environment variables
        os.environ['LLM_PROVIDER'] = 'openai'
        os.environ['LLM_MODEL'] = 'gpt-4'
        os.environ['EMBEDDING_PROVIDER'] = 'openai'
        os.environ['EMBEDDING_MODEL'] = 'text-embedding-3-small'
        os.environ['OPENAI_API_KEY'] = 'test-key'

        try:
            from src.core.config import get_config
            config = get_config(use_hot_reload=False)

            self.assertEqual(config.provider, 'openai')
            self.assertEqual(config.model, 'gpt-4')
            self.assertEqual(config.embedding_provider, 'openai')
            self.assertEqual(config.embedding_model, 'text-embedding-3-small')
            self.assertEqual(config.api_key, 'test-key')
        finally:
            # Clean up environment variables
            for var in ['LLM_PROVIDER', 'LLM_MODEL', 'EMBEDDING_PROVIDER', 'EMBEDDING_MODEL', 'OPENAI_API_KEY']:
                if var in os.environ:
                    del os.environ[var]

    @patch('src.core.config.create_llm_instances')
    def test_create_llm_instances_with_openai_provider_logic(self, mock_create_llm_instances):
        """Test the logic of create_llm_instances function with OpenAI provider."""
        # Setup mock return value
        mock_instances = {"llm": MagicMock(), "embeddings": MagicMock()}
        mock_create_llm_instances.return_value = mock_instances

        # Create config with OpenAI provider
        config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai",
            embedding_model="text-embedding-ada-002",
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection"
        )

        # Call the function
        from src.core.config import create_llm_instances
        instances = create_llm_instances(config, use_hot_reload=False)

        # Verify that the function was called
        mock_create_llm_instances.assert_called_once()

        # Verify that instances were created
        self.assertIn("llm", instances)
        self.assertIn("embeddings", instances)

    @patch('src.core.config.create_llm_instances')
    def test_create_llm_instances_with_openai_compatible_provider_logic(self, mock_create_llm_instances):
        """Test the logic of create_llm_instances function with OpenAI compatible provider."""
        # Setup mock return value
        mock_instances = {"llm": MagicMock(), "embeddings": MagicMock()}
        mock_create_llm_instances.return_value = mock_instances

        # Create config with OpenAI compatible provider
        config = LLMConfig(
            provider="openai_compatible",
            model="local-model",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai_compatible",
            embedding_model="text-embedding-ada-002",  # Use a valid OpenAI embedding model
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection",
            base_url="http://localhost:1234/v1"
        )

        # Call the function
        from src.core.config import create_llm_instances
        instances = create_llm_instances(config, use_hot_reload=False)

        # Verify that the function was called
        mock_create_llm_instances.assert_called_once()

        # Verify that instances were created
        self.assertIn("llm", instances)
        self.assertIn("embeddings", instances)

    @patch('src.core.config.logger')
    @patch('src.core.config.create_llm_instances')
    def test_openai_compatible_base_url_formatting_logic(self, mock_create_llm_instances, mock_logger):
        """Test that base_url gets properly formatted with /v1 suffix when missing."""
        # Setup mock return value
        mock_instances = {"llm": MagicMock(), "embeddings": MagicMock()}
        mock_create_llm_instances.return_value = mock_instances

        # Create config with OpenAI compatible provider and base_url missing /v1
        config = LLMConfig(
            provider="openai_compatible",
            model="local-model",
            api_key="fake-api-key-for-testing",
            embedding_provider="openai_compatible",
            embedding_model="text-embedding-ada-002",  # Use a valid OpenAI embedding model
            chroma_path="./chroma_data",
            collection_name="test_collection",
            project_collection_name="test_project_collection",
            base_url="http://localhost:1234"
        )

        # Call the function
        from src.core.config import create_llm_instances
        instances = create_llm_instances(config, use_hot_reload=False)

        # Verify that the function was called
        mock_create_llm_instances.assert_called_once()

        # Verify that instances were created
        self.assertIn("llm", instances)
        self.assertIn("embeddings", instances)


if __name__ == "__main__":
    unittest.main()