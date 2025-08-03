from groq import Groq
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import os

from app.core.exceptions import LLMError, ConfigurationError


class LLMService:
    """Service for LLM interactions and response generation"""
    
    def __init__(self, model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        self.model = model
        self._client = None
        self._initialized = False
        self._prompts_setup = False
    
    def _initialize(self):
        """Lazy initialization of the LLM service"""
        if self._initialized:
            return
            
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not self.groq_api_key:
            raise ConfigurationError(
                "GROQ_API_KEY not found in environment variables", 
                config_key="GROQ_API_KEY"
            )
        
        self._client = Groq(api_key=self.groq_api_key)
        self._initialized = True
    
    @property
    def client(self):
        """Get the Groq client instance, initializing if needed"""
        if not self._initialized:
            self._initialize()
        return self._client
    
    def _setup_prompts(self):
        """Setup all the prompt templates"""
        if self._prompts_setup:
            return
            
        # Prompt for answering user questions
        self.answer_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
                You are a helpful AI assistant. Answer questions based ONLY on the provided context.

                Instructions:
                - Use ONLY the provided context
                - Keep answers SHORT and CONCISE (max 2-3 sentences)
                - If information is not in the context, say: "I don't have enough information to answer that."
                - Be factual and direct

                Context:
                {context}

                Question:
                {question}

                Answer:
            """
        )

        self._prompts_setup = True
    
    def answer_question(self, query: str, context: str, sources: List[str] = None, metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Answer a question based on provided context
        
        Args:
            query: User's question
            context: Relevant document context
            sources: List of source file names
            metadata: List of metadata dictionaries for context chunks (optional)
            
        Returns:
            Dictionary containing answer and metadata
        """
        try:
            self._setup_prompts()
            
            # Format the prompt
            formatted_prompt = self.answer_prompt.format(
                context=context,
                question=query
            )
            
            # Generate response using Groq
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300,
                top_p=1,
                stream=False,
                stop=None,
            )
            
            # Extract the response
            answer_text = completion.choices[0].message.content
            
            # Check if the answer indicates no relevant information was found
            no_info_indicators = [
                "i don't have enough information",
                "i don't have sufficient information", 
                "no information found",
                "not enough information",
                "cannot answer",
                "unable to answer"
            ]
            
            has_relevant_info = not any(indicator in answer_text.lower() for indicator in no_info_indicators)
            
            # Only add sources if we have relevant information
            if sources and has_relevant_info:
                source_text = f"\n\nSource: {sources[0]}"  # Only show the most relevant source
                answer_text += source_text
            
            # Prepare response with optional metadata context
            response = {
                "answer": answer_text,
                "model": self.model,
                "has_justification": has_relevant_info,  # Only true if we have relevant information
                "sources": sources if has_relevant_info else []  # Only include sources if relevant
            }
            
            # Add metadata context if available
            if metadata:
                response["context_metadata"] = self._extract_context_metadata(metadata)
            
            return response
            
        except Exception as e:
            raise LLMError(f"Error generating answer: {str(e)}", model=self.model)
    
    def _extract_context_metadata(self, metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract key metadata for response context
        
        Args:
            metadata: List of metadata dictionaries
            
        Returns:
            Dictionary with key metadata information
        """
        if not metadata:
            return {}
        
        context_metadata = {
            "sources": list(set([m.get('source', 'Unknown') for m in metadata])),
            "total_chunks": len(metadata)
        }
        
        # Add content types if available
        content_types = list(set([m.get('content_type', 'general_text') for m in metadata]))
        if content_types:
            context_metadata["content_types"] = content_types
        
        # Add document categories if available
        categories = list(set([m.get('document_category', 'other') for m in metadata]))
        if categories:
            context_metadata["document_categories"] = categories
        
        # Add semantic tags if available
        all_tags = []
        for m in metadata:
            tags = m.get('semantic_tags', [])
            all_tags.extend(tags)
        unique_tags = list(set(all_tags))
        if unique_tags:
            context_metadata["semantic_tags"] = unique_tags[:10]  # Limit to 10 tags
        
        return context_metadata


# Global instance
llm_service = LLMService() 