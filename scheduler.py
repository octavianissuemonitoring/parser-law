#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scheduler pentru scraping automat al actelor legislative.
Suportă configurare flexibilă prin variabile de mediu sau config file.

NEW: Includes AI processing and export automation.
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Import scraper
from scraper_legislatie import LegislationScraper

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ScraperSchedulerConfig:
    """Configuration pentru scheduler."""
    
    def __init__(self):
        """Încarcă configurația din environment variables sau valori default."""
        
        # General settings
        self.enabled = os.getenv('SCRAPER_ENABLED', 'true').lower() == 'true'
        self.schedule_type = os.getenv('SCRAPER_SCHEDULE_TYPE', 'daily_weekdays')
        
        # Daily weekdays settings
        self.hour = int(os.getenv('SCRAPER_HOUR', '14'))
        self.days = os.getenv('SCRAPER_DAYS', '1-4')  # Monday-Thursday
        
        # Weekly settings
        self.weekly_day = int(os.getenv('SCRAPER_WEEKLY_DAY', '1'))  # Monday
        self.weekly_hour = int(os.getenv('SCRAPER_WEEKLY_HOUR', '10'))
        
        # Custom cron
        self.cron_expression = os.getenv('SCRAPER_CRON_EXPRESSION', '0 14 * * 1-4')
        
        # Scraper settings
        self.delay = float(os.getenv('SCRAPER_DELAY', '2.0'))
        self.links_file = os.getenv('SCRAPER_LINKS_FILE', 'linkuri_legislatie.txt')
        self.output_dir = os.getenv('SCRAPER_OUTPUT_DIR', 'rezultate')
        
        # Import settings
        self.auto_import = os.getenv('SCRAPER_AUTO_IMPORT', 'true').lower() == 'true'
        self.api_url = os.getenv('SCRAPER_API_URL', 'http://localhost:8000')
        
        # Cleanup settings
        self.auto_cleanup = os.getenv('SCRAPER_AUTO_CLEANUP', 'true').lower() == 'true'
        
        # AI Processing settings
        self.ai_enabled = os.getenv('AI_PROCESSING_ENABLED', 'true').lower() == 'true'
        self.ai_schedule = os.getenv('AI_PROCESSING_SCHEDULE', '*/30 * * * *')  # Every 30 minutes
        self.ai_batch_size = int(os.getenv('AI_PROCESSING_BATCH_SIZE', '10'))
        self.ai_batch_delay = float(os.getenv('AI_PROCESSING_DELAY', '1.0'))
        
        # Export settings
        self.export_enabled = os.getenv('EXPORT_ENABLED', 'true').lower() == 'true'
        self.export_schedule = os.getenv('EXPORT_SCHEDULE', '0 * * * *')  # Every hour
        self.export_batch_size = int(os.getenv('EXPORT_BATCH_SIZE', '10'))
        self.export_sync_enabled = os.getenv('EXPORT_SYNC_ENABLED', 'true').lower() == 'true'
        self.export_sync_schedule = os.getenv('EXPORT_SYNC_SCHEDULE', '30 * * * *')  # Every hour at :30
    
    def get_cron_trigger(self) -> CronTrigger:
        """
        Generează CronTrigger bazat pe configurație.
        
        Returns:
            CronTrigger object pentru APScheduler
        """
        if self.schedule_type == 'daily_weekdays':
            # Format: "minute hour day month day_of_week"
            # Example: "0 14 * * 1-4" = 14:00 Monday-Thursday
            return CronTrigger.from_crontab(f"0 {self.hour} * * {self.days}")
        
        elif self.schedule_type == 'weekly':
            # Run once per week
            return CronTrigger.from_crontab(f"0 {self.weekly_hour} * * {self.weekly_day}")
        
        elif self.schedule_type == 'custom':
            # Custom cron expression
            return CronTrigger.from_crontab(self.cron_expression)
        
        else:
            raise ValueError(f"Unknown schedule type: {self.schedule_type}")
    
    def __str__(self) -> str:
        """String representation pentru debugging."""
        if self.schedule_type == 'daily_weekdays':
            schedule = f"Daily at {self.hour}:00, days {self.days}"
        elif self.schedule_type == 'weekly':
            schedule = f"Weekly on day {self.weekly_day} at {self.weekly_hour}:00"
        else:
            schedule = f"Custom: {self.cron_expression}"
        
        return f"ScraperScheduler(enabled={self.enabled}, schedule={schedule})"


class ScraperScheduler:
    """Scheduler pentru scraping automat."""
    
    def __init__(self, config: Optional[ScraperSchedulerConfig] = None):
        """
        Inițializează scheduler-ul.
        
        Args:
            config: Configurație (default: citește din env vars)
        """
        self.config = config or ScraperSchedulerConfig()
        self.scheduler = BlockingScheduler()
        self.scraper = LegislationScraper(
            links_file=self.config.links_file,
            output_dir=self.config.output_dir
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """Listener pentru evenimente job."""
        if event.exception:
            logger.error(f"❌ Job failed with exception: {event.exception}")
        else:
            logger.info(f"✅ Job executed successfully")
    
    def run_scraping_job(self):
        """
        Job principal de scraping.
        Rulează scraper-ul și opțional face import în DB.
        """
        try:
            logger.info("="*70)
            logger.info(f"🚀 Starting scheduled scraping job at {datetime.now()}")
            logger.info("="*70)
            
            # Run scraper
            logger.info("📥 Running scraper...")
            start_time = time.time()
            
            self.scraper.run(delay_seconds=self.config.delay)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Scraping completed in {elapsed:.2f} seconds")
            
            # Auto-import to database
            if self.config.auto_import:
                logger.info("📤 Auto-importing to database...")
                self._run_import()
            
            # Auto-cleanup old files
            if self.config.auto_cleanup:
                logger.info("🧹 Running auto-cleanup...")
                self._run_cleanup()
            
            logger.info("="*70)
            logger.info(f"🏁 Scheduled job completed at {datetime.now()}")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ Error in scraping job: {e}", exc_info=True)
            raise
    
    def _run_import(self):
        """Rulează import în database via API."""
        try:
            import requests
            
            url = f"{self.config.api_url}/api/v1/acte/import"
            params = {"rezultate_dir": f"../{self.config.output_dir}"}
            
            logger.info(f"📤 POST {url}")
            response = requests.post(url, params=params, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Import result: {result}")
            
            if result.get('success'):
                logger.info(f"   ✅ New acts: {result.get('imported_acts', 0)}")
                logger.info(f"   🔄 Updated acts: {result.get('updated_acts', 0)}")
                logger.info(f"   📊 Total articles: {result.get('imported_articles', 0)}")
            else:
                logger.warning(f"⚠️  Import returned success=false")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to import to database: {e}")
        except Exception as e:
            logger.error(f"❌ Error during import: {e}", exc_info=True)
    
    def _run_cleanup(self):
        """Rulează cleanup automat după import."""
        import subprocess
        
        try:
            cmd = ["python", "cleanup_files.py", "--execute", "--quiet"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse output pentru număr de fișiere șterse
                output = result.stdout.strip()
                if output:
                    logger.info(f"✅ {output}")
                else:
                    logger.info("✅ Cleanup completed (no duplicates)")
            else:
                logger.warning(f"⚠️  Cleanup failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error("❌ Cleanup timeout (>60s)")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    def run_ai_processing_job(self):
        """
        Job pentru procesare AI automată.
        Procesează articolele pending cu AI pentru extragere issues.
        """
        try:
            logger.info("="*70)
            logger.info(f"🤖 Starting AI processing job at {datetime.now()}")
            logger.info("="*70)
            
            # Import inside function to avoid circular imports
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'db_service'))
            from app.services.ai_service import AIService
            from app.database import async_sessionmaker
            
            async def process():
                ai_service = AIService()
                stats = await ai_service.process_pending_articole(
                    limit=self.config.ai_batch_size,
                    batch_delay=self.config.ai_batch_delay
                )
                return stats
            
            start_time = time.time()
            stats = asyncio.run(process())
            elapsed = time.time() - start_time
            
            logger.info(f"✅ AI processing completed in {elapsed:.2f} seconds")
            logger.info(f"   ✅ Success: {stats['success']}")
            logger.info(f"   ❌ Errors: {stats['error']}")
            logger.info(f"   ⏭️  Skipped: {stats['skipped']}")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ Error in AI processing job: {e}", exc_info=True)
            raise
    
    def run_export_job(self):
        """
        Job pentru export automat către Issue Monitoring.
        Exportă actele procesate de AI.
        """
        try:
            logger.info("="*70)
            logger.info(f"📤 Starting export job at {datetime.now()}")
            logger.info("="*70)
            
            # Import inside function
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'db_service'))
            from app.services.export_service import ExportService
            from app.database import async_sessionmaker
            
            async def export():
                export_service = ExportService()
                stats = await export_service.export_to_issue_monitoring(
                    session=None,
                    act_id=None,
                    limit=self.config.export_batch_size
                )
                return stats
            
            start_time = time.time()
            
            # Need to create session properly
            async def run_export():
                from app.database import async_sessionmaker
                async with async_sessionmaker() as session:
                    export_service = ExportService()
                    stats = await export_service.export_to_issue_monitoring(
                        session=session,
                        act_id=None,
                        limit=self.config.export_batch_size
                    )
                    return stats
            
            stats = asyncio.run(run_export())
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Export completed in {elapsed:.2f} seconds")
            logger.info(f"   ✅ Success: {stats['success']}")
            logger.info(f"   ❌ Errors: {stats['error']}")
            logger.info(f"   ⏭️  Skipped: {stats['skipped']}")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ Error in export job: {e}", exc_info=True)
            raise
    
    def run_export_sync_job(self):
        """
        Job pentru sincronizare updates către Issue Monitoring.
        Sincronizează articole/anexe noi pentru acte deja exportate.
        """
        try:
            logger.info("="*70)
            logger.info(f"🔄 Starting export sync job at {datetime.now()}")
            logger.info("="*70)
            
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'db_service'))
            from app.services.export_service import ExportService
            from app.database import async_sessionmaker
            
            async def run_sync():
                async with async_sessionmaker() as session:
                    export_service = ExportService()
                    stats = await export_service.sync_updates(
                        session=session,
                        limit=50
                    )
                    return stats
            
            start_time = time.time()
            stats = asyncio.run(run_sync())
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Sync completed in {elapsed:.2f} seconds")
            logger.info(f"   ✅ Success: {stats['success']}")
            logger.info(f"   ❌ Errors: {stats['error']}")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ Error in sync job: {e}", exc_info=True)
            raise
    
    def start(self):
        """Pornește scheduler-ul."""
        if not self.config.enabled:
            logger.warning("⚠️  Scheduler is DISABLED (SCRAPER_ENABLED=false)")
            logger.info("To enable, set SCRAPER_ENABLED=true")
            return
        
        logger.info("="*70)
        logger.info("🕐 Legislative Acts Scraper Scheduler")
        logger.info("="*70)
        logger.info(f"Configuration: {self.config}")
        logger.info(f"Links file: {self.config.links_file}")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info(f"Delay between requests: {self.config.delay}s")
        logger.info(f"Auto-import: {self.config.auto_import}")
        if self.config.auto_import:
            logger.info(f"API URL: {self.config.api_url}")
        logger.info(f"AI Processing: {self.config.ai_enabled}")
        logger.info(f"Export: {self.config.export_enabled}")
        logger.info("="*70)
        
        # Add job to scheduler
        trigger = self.config.get_cron_trigger()
        self.scheduler.add_job(
            self.run_scraping_job,
            trigger=trigger,
            id='scraping_job',
            name='Legislative Acts Scraping',
            misfire_grace_time=3600,  # 1 hour grace period
            coalesce=True,  # Combine missed runs into one
            max_instances=1  # Only one instance at a time
        )
        
        # Add AI processing job
        if self.config.ai_enabled:
            ai_trigger = CronTrigger.from_crontab(self.config.ai_schedule)
            self.scheduler.add_job(
                self.run_ai_processing_job,
                trigger=ai_trigger,
                id='ai_processing_job',
                name='AI Processing',
                misfire_grace_time=1800,  # 30 minutes grace
                coalesce=True,
                max_instances=1
            )
            logger.info(f"✅ AI processing job added (schedule: {self.config.ai_schedule})")
        
        # Add export job
        if self.config.export_enabled:
            export_trigger = CronTrigger.from_crontab(self.config.export_schedule)
            self.scheduler.add_job(
                self.run_export_job,
                trigger=export_trigger,
                id='export_job',
                name='Export to Issue Monitoring',
                misfire_grace_time=1800,
                coalesce=True,
                max_instances=1
            )
            logger.info(f"✅ Export job added (schedule: {self.config.export_schedule})")
        
        # Add export sync job
        if self.config.export_enabled and self.config.export_sync_enabled:
            sync_trigger = CronTrigger.from_crontab(self.config.export_sync_schedule)
            self.scheduler.add_job(
                self.run_export_sync_job,
                trigger=sync_trigger,
                id='export_sync_job',
                name='Export Sync Updates',
                misfire_grace_time=1800,
                coalesce=True,
                max_instances=1
            )
            logger.info(f"✅ Export sync job added (schedule: {self.config.export_sync_schedule})")
        
        # Print next run time
        try:
            jobs = self.scheduler.get_jobs()
            if jobs:
                logger.info(f"⏰ Scheduled jobs: {len(jobs)}")
                for job in jobs:
                    if hasattr(job, 'next_run_time'):
                        logger.info(f"   - {job.id}: next run at {job.next_run_time}")
                    else:
                        logger.info(f"   - {job.id}: scheduled")
        except Exception as e:
            logger.warning(f"Could not retrieve job schedule info: {e}")
        
        logger.info(f"🔄 Scheduler started. Waiting for scheduled time...")
        logger.info("   Press Ctrl+C to stop")
        logger.info("="*70)
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n👋 Scheduler stopped by user")
            self.scheduler.shutdown()
    
    def run_now(self):
        """Rulează job-ul imediat (pentru testing)."""
        logger.info("🚀 Running scraping job NOW (manual trigger)...")
        self.run_scraping_job()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scheduler pentru scraping automat al actelor legislative',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple de utilizare:

  # Rulează scheduler cu setări din environment variables
  python scheduler.py

  # Rulează imediat (test mode)
  python scheduler.py --now

  # Afișează configurația curentă
  python scheduler.py --show-config

Configurare prin environment variables:

  # Luni-Joi la ora 14:00
  export SCRAPER_SCHEDULE_TYPE=daily_weekdays
  export SCRAPER_HOUR=14
  export SCRAPER_DAYS=1-4

  # Doar Luni la ora 10:00
  export SCRAPER_SCHEDULE_TYPE=weekly
  export SCRAPER_WEEKLY_DAY=1
  export SCRAPER_WEEKLY_HOUR=10

  # Custom cron
  export SCRAPER_SCHEDULE_TYPE=custom
  export SCRAPER_CRON_EXPRESSION="0 8,14,20 * * 1-5"
        """
    )
    
    parser.add_argument(
        '--now',
        action='store_true',
        help='Rulează scraping-ul imediat (nu așteaptă schedule)'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Afișează configurația curentă și iese'
    )
    
    parser.add_argument(
        '--test-cron',
        metavar='EXPRESSION',
        help='Testează o expresie cron și afișează următoarele 5 rulări'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = ScraperSchedulerConfig()
    
    # Show config
    if args.show_config:
        print("="*70)
        print("📋 Current Scheduler Configuration")
        print("="*70)
        print(f"Enabled: {config.enabled}")
        print(f"Schedule Type: {config.schedule_type}")
        print()
        
        if config.schedule_type == 'daily_weekdays':
            print(f"Schedule: Daily at {config.hour}:00")
            print(f"Days: {config.days}")
            print(f"Cron: 0 {config.hour} * * {config.days}")
        elif config.schedule_type == 'weekly':
            print(f"Schedule: Weekly on day {config.weekly_day}")
            print(f"Hour: {config.weekly_hour}:00")
            print(f"Cron: 0 {config.weekly_hour} * * {config.weekly_day}")
        else:
            print(f"Schedule: Custom")
            print(f"Cron: {config.cron_expression}")
        
        print()
        print(f"Delay: {config.delay}s")
        print(f"Links File: {config.links_file}")
        print(f"Output Dir: {config.output_dir}")
        print(f"Auto Import: {config.auto_import}")
        if config.auto_import:
            print(f"API URL: {config.api_url}")
        print("="*70)
        
        # Show next runs
        try:
            trigger = config.get_cron_trigger()
            from datetime import datetime, timedelta
            
            print("\n⏰ Next 5 scheduled runs:")
            current = datetime.now()
            for i in range(5):
                next_time = trigger.get_next_fire_time(None, current)
                if next_time:
                    print(f"   {i+1}. {next_time.strftime('%Y-%m-%d %H:%M:%S %A')}")
                    current = next_time + timedelta(seconds=1)
                else:
                    break
        except Exception as e:
            print(f"\n⚠️  Error calculating next runs: {e}")
        
        return
    
    # Test cron expression
    if args.test_cron:
        print(f"🧪 Testing cron expression: {args.test_cron}")
        try:
            trigger = CronTrigger.from_crontab(args.test_cron)
            from datetime import datetime, timedelta
            
            print("\n⏰ Next 5 runs:")
            current = datetime.now()
            for i in range(5):
                next_time = trigger.get_next_fire_time(None, current)
                if next_time:
                    print(f"   {i+1}. {next_time.strftime('%Y-%m-%d %H:%M:%S %A')}")
                    current = next_time + timedelta(seconds=1)
                else:
                    break
        except Exception as e:
            print(f"❌ Invalid cron expression: {e}")
        return
    
    # Create scheduler
    scheduler = ScraperScheduler(config)
    
    # Run now or start scheduler
    if args.now:
        scheduler.run_now()
    else:
        scheduler.start()


if __name__ == "__main__":
    main()
