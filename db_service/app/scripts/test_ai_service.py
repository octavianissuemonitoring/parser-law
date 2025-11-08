"""
Test script for AIService - Process articles with AI.

Usage:
    python -m app.scripts.test_ai_service
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.ai_service import AIService
from app.database import async_sessionmaker


async def test_extract_issues():
    """Test issue extraction."""
    print("\n=== Test: Extract Issues ===\n")
    
    # Sample legislative text
    text = """
    Art. 5. (1) Contribuabilii sunt obligați să depună declarația fiscală până
    la data de 25 a lunii următoare.
    (2) Nedepunerea declarației în termen atrage aplicarea unei amenzi de la
    500 lei la 1000 lei.
    (3) În cazul depunerii declarației cu întârziere mai mare de 30 de zile,
    amenda se majorează cu 50%.
    """
    
    context = "Legea 123/2024 - Codul fiscal"
    
    ai_service = AIService(provider="openai")
    issues = await ai_service.extract_issues(text, context)
    
    print(f"Found {len(issues)} issues:")
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['denumire']}")
        print(f"   Description: {issue['descriere'][:100]}...")
        print(f"   Confidence: {issue['confidence_score']}")


async def test_generate_metadata():
    """Test metadata generation."""
    print("\n=== Test: Generate Metadata ===\n")
    
    text = """
    Art. 10. (1) Societățile comerciale sunt obligate să țină evidența
    contabilă conform standardelor internaționale.
    (2) Documentele contabile se păstrează minimum 10 ani.
    """
    
    context = "Legea contabilității"
    
    ai_service = AIService(provider="openai")
    metadate = await ai_service.generate_metadata(text, context, max_length=200)
    
    print(f"Generated metadata:\n{metadate}")


async def test_process_articol():
    """Test processing a real article from database."""
    print("\n=== Test: Process Article from DB ===\n")
    
    ai_service = AIService(provider="openai")
    
    async with async_sessionmaker() as session:
        # Process first pending article
        success, error = await ai_service.process_articol(1, session)
        
        if success:
            print("✓ Article processed successfully!")
        else:
            print(f"✗ Failed to process article: {error}")


async def test_batch_processing():
    """Test batch processing of pending articles."""
    print("\n=== Test: Batch Processing ===\n")
    
    ai_service = AIService(provider="openai")
    stats = await ai_service.process_pending_articole(limit=5, batch_delay=2.0)
    
    print(f"\nProcessing statistics:")
    print(f"  Success: {stats['success']}")
    print(f"  Error: {stats['error']}")
    print(f"  Skipped: {stats['skipped']}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AIService Test Suite")
    print("=" * 60)
    
    try:
        # Uncomment tests you want to run
        
        await test_extract_issues()
        await test_generate_metadata()
        
        # These require database access
        # await test_process_articol()
        # await test_batch_processing()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
