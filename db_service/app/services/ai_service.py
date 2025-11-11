"""
AI Service - Process legislation with OpenAI/Claude for issue extraction and metadata generation.
"""
import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ActLegislativ, Articol, Anexa, Issue
from app.database import async_sessionmaker


class AIService:
    """
    Service for AI-powered processing of legislation.
    
    Capabilities:
    - Extract issues/problems from legislative text
    - Generate metadata/summaries for acts, articles, and annexes
    - Batch processing with rate limiting
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        provider: str = "openai",  # "openai" or "anthropic"
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize AI service.
        
        Args:
            provider: AI provider ("openai" or "anthropic")
            model: Model to use (defaults: gpt-4o for OpenAI, claude-3-5-sonnet for Anthropic)
            api_key: API key (defaults to env var)
            max_retries: Maximum retry attempts on failure
            timeout: Request timeout in seconds
        """
        self.provider = provider.lower()
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize API client
        if self.provider == "openai":
            import openai
            self.model = model or "gpt-4o"
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            
        elif self.provider == "anthropic":
            import anthropic
            self.model = model or "claude-3-5-sonnet-20241022"
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")
    
    async def extract_issues(
        self,
        text: str,
        context: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Extract issues/problems from legislative text using AI.
        
        Args:
            text: Legislative text to analyze
            context: Additional context (e.g., act title)
            
        Returns:
            List of issues with structure:
            [
                {
                    "denumire": "Issue title",
                    "descriere": "Detailed description",
                    "confidence_score": 0.95
                }
            ]
        """
        prompt = self._build_issue_extraction_prompt(text, context)
        
        try:
            response = await self._call_ai(
                system_message="You are an expert legal analyst specialized in Romanian legislation. Extract key issues, problems, or important topics from legislative texts.",
                user_message=prompt,
                response_format="json"
            )
            
            # Parse JSON response
            issues_data = json.loads(response)
            
            # Validate and normalize structure
            issues = []
            for issue in issues_data.get("issues", []):
                issues.append({
                    "denumire": issue.get("title", "")[:256],  # Max 256 chars
                    "descriere": issue.get("description", ""),
                    "confidence_score": float(issue.get("confidence", 0.8))
                })
            
            return issues
            
        except Exception as e:
            print(f"Error extracting issues: {e}")
            return []
    
    async def generate_metadata(
        self,
        text: str,
        context: Optional[str] = None,
        max_length: int = 500
    ) -> str:
        """
        Generate summary/metadata for legislative text using AI.
        
        Args:
            text: Legislative text to summarize
            context: Additional context (e.g., act title)
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        prompt = self._build_metadata_prompt(text, context, max_length)
        
        try:
            response = await self._call_ai(
                system_message="You are an expert legal analyst specialized in Romanian legislation. Provide concise, accurate summaries of legislative texts.",
                user_message=prompt
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating metadata: {e}")
            return ""
    
    async def process_articol(
        self,
        articol_id: int,
        session: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single article: extract issues and generate metadata.
        
        Args:
            articol_id: Article ID to process
            session: Database session
            
        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            # Fetch article with act for context
            result = await session.execute(
                select(Articol)
                .options(selectinload(Articol.act))
                .where(Articol.id == articol_id)
            )
            articol = result.scalar_one_or_none()
            
            if not articol:
                return False, f"Article {articol_id} not found"
            
            # Update status to processing
            articol.ai_status = "processing"
            await session.commit()
            
            # Build context
            context = f"{articol.act.tip_act} {articol.act.nr_act}/{articol.act.an_act}"
            
            # Extract issues
            issues_data = await self.extract_issues(articol.text_articol, context)
            
            # Create Issue objects and associate with article
            for issue_data in issues_data:
                # Check if issue already exists
                result = await session.execute(
                    select(Issue).where(Issue.denumire == issue_data["denumire"])
                )
                issue = result.scalar_one_or_none()
                
                if not issue:
                    issue = Issue(
                        denumire=issue_data["denumire"],
                        descriere=issue_data["descriere"],
                        source="ai",
                        confidence_score=issue_data["confidence_score"]
                    )
                    session.add(issue)
                
                # Associate issue with article
                if issue not in articol.issues:
                    articol.issues.append(issue)
            
            # Generate metadata
            metadate = await self.generate_metadata(articol.text_articol, context)
            articol.metadate = metadate
            
            # Update status
            articol.ai_status = "completed"
            articol.ai_processed_at = datetime.utcnow()
            articol.ai_error = None
            
            await session.commit()
            return True, None
            
        except Exception as e:
            # Rollback and update error status
            await session.rollback()
            
            try:
                articol.ai_status = "error"
                articol.ai_error = str(e)[:500]  # Truncate error
                await session.commit()
            except:
                pass
            
            return False, str(e)
    
    async def process_pending_articole(
        self,
        limit: int = 10,
        batch_delay: float = 1.0
    ) -> Dict[str, int]:
        """
        Process pending articles in batch.
        
        Args:
            limit: Maximum number of articles to process
            batch_delay: Delay between items (seconds) for rate limiting
            
        Returns:
            Statistics: {"success": 5, "error": 2, "skipped": 0}
        """
        stats = {"success": 0, "error": 0, "skipped": 0}
        
        async with async_sessionmaker() as session:
            # Fetch pending articles
            result = await session.execute(
                select(Articol.id)
                .where(Articol.ai_status.in_(["pending", "error"]))
                .limit(limit)
            )
            articol_ids = [row[0] for row in result.all()]
            
            print(f"Processing {len(articol_ids)} articles...")
            
            for articol_id in articol_ids:
                success, error = await self.process_articol(articol_id, session)
                
                if success:
                    stats["success"] += 1
                    print(f"✓ Article {articol_id} processed")
                else:
                    stats["error"] += 1
                    print(f"✗ Article {articol_id} failed: {error}")
                
                # Rate limiting
                await asyncio.sleep(batch_delay)
        
        return stats
    
    async def _call_ai(
        self,
        system_message: str,
        user_message: str,
        response_format: str = "text"
    ) -> str:
        """
        Call AI provider with retry logic.
        
        Args:
            system_message: System prompt
            user_message: User prompt
            response_format: "text" or "json"
            
        Returns:
            AI response text
        """
        for attempt in range(self.max_retries):
            try:
                if self.provider == "openai":
                    kwargs = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ],
                        "timeout": self.timeout
                    }
                    
                    if response_format == "json":
                        kwargs["response_format"] = {"type": "json_object"}
                    
                    response = await self.client.chat.completions.create(**kwargs)
                    return response.choices[0].message.content
                    
                elif self.provider == "anthropic":
                    response = await self.client.messages.create(
                        model=self.model,
                        max_tokens=4096,
                        system=system_message,
                        messages=[
                            {"role": "user", "content": user_message}
                        ],
                        timeout=self.timeout
                    )
                    return response.content[0].text
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"AI call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _build_issue_extraction_prompt(self, text: str, context: Optional[str]) -> str:
        """Build prompt for issue extraction."""
        prompt = f"""Analyze the following Romanian legislative text and extract key issues, problems, or important topics.

{f"Context: {context}" if context else ""}

Legislative Text:
{text[:4000]}  # Truncate to avoid token limits

Return a JSON object with this structure:
{{
  "issues": [
    {{
      "title": "Brief issue title (max 100 chars)",
      "description": "Detailed description of the issue",
      "confidence": 0.95  // Your confidence in this extraction (0.0-1.0)
    }}
  ]
}}

Focus on:
- Legal obligations and requirements
- Rights and restrictions
- Penalties and sanctions
- Important deadlines or conditions
- Areas of potential legal risk

Return ONLY valid JSON, no additional text."""
        
        return prompt
    
    def _build_metadata_prompt(
        self,
        text: str,
        context: Optional[str],
        max_length: int
    ) -> str:
        """Build prompt for metadata generation."""
        prompt = f"""Summarize the following Romanian legislative text in clear, concise Romanian.

{f"Context: {context}" if context else ""}

Legislative Text:
{text[:4000]}  # Truncate to avoid token limits

Requirements:
- Maximum {max_length} characters
- Use clear, professional Romanian
- Focus on the main legal implications
- Highlight key obligations, rights, or restrictions
- Be objective and factual

Summary:"""
        
        return prompt
