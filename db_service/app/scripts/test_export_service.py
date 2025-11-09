"""
Test script for ExportService - Export to Issue Monitoring.

Usage:
    python -m app.scripts.test_export_service
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.export_service import ExportService
from app.database import async_sessionmaker


async def test_build_package():
    """Test building export package."""
    print("\n=== Test: Build Export Package ===\n")
    
    export_service = ExportService()
    
    async with async_sessionmaker() as session:
        # Build packages for acts ready to export
        packages = await export_service.build_export_package(
            session=session,
            limit=2
        )
        
        print(f"Built {len(packages)} packages:")
        for i, package in enumerate(packages, 1):
            print(f"\n{i}. Act: {package['act']['titlu']}")
            print(f"   ID: {package['act']['id']}")
            print(f"   Articles: {len(package['articles'])}")
            print(f"   Annexes: {len(package['annexes'])}")
            print(f"   Issues: {len(package['issues'])}")
            
            if package['issues']:
                print(f"\n   Sample Issues:")
                for issue in package['issues'][:3]:
                    print(f"   - {issue['denumire']} (confidence: {issue['confidence_score']})")


async def test_export():
    """Test exporting to Issue Monitoring."""
    print("\n=== Test: Export to Issue Monitoring ===\n")
    
    export_service = ExportService()
    
    # Check if API key is configured
    if not export_service.api_key:
        print("⚠ ISSUE_MONITORING_API_KEY not configured")
        print("Set environment variable to test actual export:")
        print("export ISSUE_MONITORING_API_KEY='your-api-key'")
        return
    
    async with async_sessionmaker() as session:
        # Export acts
        stats = await export_service.export_to_issue_monitoring(
            session=session,
            limit=2
        )
        
        print(f"\nExport statistics:")
        print(f"  Success: {stats['success']}")
        print(f"  Error: {stats['error']}")
        print(f"  Skipped: {stats['skipped']}")


async def test_sync_updates():
    """Test syncing updates for already exported acts."""
    print("\n=== Test: Sync Updates ===\n")
    
    export_service = ExportService()
    
    if not export_service.api_key:
        print("⚠ ISSUE_MONITORING_API_KEY not configured")
        return
    
    async with async_sessionmaker() as session:
        stats = await export_service.sync_updates(
            session=session,
            limit=5
        )
        
        print(f"\nSync statistics:")
        print(f"  Success: {stats['success']}")
        print(f"  Error: {stats['error']}")


async def test_specific_act():
    """Test exporting a specific act by ID."""
    print("\n=== Test: Export Specific Act ===\n")
    
    act_id = input("Enter act ID to export (or press Enter to skip): ").strip()
    
    if not act_id:
        print("Skipped")
        return
    
    try:
        act_id = int(act_id)
    except ValueError:
        print("Invalid act ID")
        return
    
    export_service = ExportService()
    
    async with async_sessionmaker() as session:
        # First build package to preview
        packages = await export_service.build_export_package(
            session=session,
            act_id=act_id
        )
        
        if not packages:
            print(f"No package found for act ID {act_id}")
            return
        
        package = packages[0]
        print(f"\nAct: {package['act']['titlu']}")
        print(f"Articles: {len(package['articles'])}")
        print(f"Issues: {len(package['issues'])}")
        
        proceed = input("\nProceed with export? (y/n): ").strip().lower()
        
        if proceed == 'y':
            stats = await export_service.export_to_issue_monitoring(
                session=session,
                act_id=act_id
            )
            print(f"\nResult: {stats}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ExportService Test Suite")
    print("=" * 60)
    
    try:
        # Test package building (always works)
        await test_build_package()
        
        # Test export (requires API key)
        # await test_export()
        
        # Test sync (requires API key)
        # await test_sync_updates()
        
        # Test specific act export
        # await test_specific_act()
        
        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
