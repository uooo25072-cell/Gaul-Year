import os
import shutil
from datetime import datetime
from config import config

class BackupService:
    @staticmethod
    def create_backup() -> str:
        """Create a timestamped backup copy of the SQLite database."""
        db_path = config.DATABASE_PATH
        if not os.path.exists(db_path):
            raise FileNotFoundError("Database file does not exist.")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_filename = f"GameZone_Backup_{timestamp}.db"
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        target_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, target_path)
        return target_path

    @staticmethod
    def restore_backup(source_file_path: str) -> bool:
        """Replace active SQLite DB file with provided backup file."""
        db_path = config.DATABASE_PATH
        if not os.path.exists(source_file_path):
            return False

        # Create temporary safety copy before restoring
        safety_copy = f"{db_path}.before_restore.bak"
        if os.path.exists(db_path):
            shutil.copy2(db_path, safety_copy)

        try:
            shutil.copy2(source_file_path, db_path)
            if os.path.exists(safety_copy):
                os.remove(safety_copy)
            return True
        except Exception as e:
            if os.path.exists(safety_copy):
                shutil.copy2(safety_copy, db_path)
            raise e
