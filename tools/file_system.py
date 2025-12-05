"""
File System Tools - Complete file manipulation capabilities for the agentic AI.
Allows the agent to create, read, modify, delete files and manage directories.
"""

import os
import shutil
import difflib
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json
import fnmatch


@dataclass
class FileOperation:
    """Record of a file operation."""
    operation: str  # create, read, update, delete, move, copy
    path: str
    success: bool
    message: str
    timestamp: datetime
    backup_path: Optional[str] = None


class FileSystemTools:
    """
    Comprehensive file system manipulation tools for agentic AI.
    
    Features:
    - Create, read, update, delete files
    - Directory management
    - Safe operations with backups
    - Diff generation and patching
    - File search and filtering
    - Undo support via backups
    """

    def __init__(
        self,
        workspace_root: str = ".",
        backup_dir: str = ".agent_backups",
        enable_backups: bool = True,
        sandbox_mode: bool = False,  # If True, restricts to workspace only
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.backup_dir = self.workspace_root / backup_dir
        self.enable_backups = enable_backups
        self.sandbox_mode = sandbox_mode
        self.operation_history: list[FileOperation] = []
        
        if enable_backups:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and resolve a path, ensuring it's safe."""
        resolved = Path(path).resolve()
        
        if self.sandbox_mode:
            try:
                resolved.relative_to(self.workspace_root)
            except ValueError:
                raise PermissionError(
                    f"Path {path} is outside workspace. "
                    f"Sandbox mode restricts access to {self.workspace_root}"
                )
        
        return resolved

    def _create_backup(self, path: Path) -> Optional[str]:
        """Create a backup of a file before modification."""
        if not self.enable_backups or not path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(path, backup_path)
        return str(backup_path)

    def _log_operation(
        self,
        operation: str,
        path: str,
        success: bool,
        message: str,
        backup_path: Optional[str] = None,
    ):
        """Log a file operation."""
        self.operation_history.append(FileOperation(
            operation=operation,
            path=path,
            success=success,
            message=message,
            timestamp=datetime.now(),
            backup_path=backup_path,
        ))

    # ==================== READ OPERATIONS ====================

    def read_file(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read the contents of a file.
        
        Args:
            path: File path to read
            encoding: File encoding
            
        Returns:
            File contents as string
        """
        path = self._validate_path(path)
        
        try:
            content = path.read_text(encoding=encoding)
            self._log_operation("read", str(path), True, f"Read {len(content)} chars")
            return content
        except Exception as e:
            self._log_operation("read", str(path), False, str(e))
            raise

    def read_file_lines(
        self,
        path: Union[str, Path],
        start_line: int = 1,
        end_line: Optional[int] = None,
    ) -> list[str]:
        """
        Read specific lines from a file.
        
        Args:
            path: File path
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (inclusive)
            
        Returns:
            List of lines
        """
        content = self.read_file(path)
        lines = content.splitlines()
        
        start_idx = max(0, start_line - 1)
        end_idx = end_line if end_line else len(lines)
        
        return lines[start_idx:end_idx]

    def file_exists(self, path: Union[str, Path]) -> bool:
        """Check if a file exists."""
        try:
            path = self._validate_path(path)
            return path.is_file()
        except PermissionError:
            return False

    def dir_exists(self, path: Union[str, Path]) -> bool:
        """Check if a directory exists."""
        try:
            path = self._validate_path(path)
            return path.is_dir()
        except PermissionError:
            return False

    def list_directory(
        self,
        path: Union[str, Path] = ".",
        pattern: str = "*",
        recursive: bool = False,
    ) -> list[dict]:
        """
        List contents of a directory.
        
        Args:
            path: Directory path
            pattern: Glob pattern to filter
            recursive: Whether to list recursively
            
        Returns:
            List of file/directory info dicts
        """
        path = self._validate_path(path)
        
        if recursive:
            items = list(path.rglob(pattern))
        else:
            items = list(path.glob(pattern))
        
        results = []
        for item in items:
            try:
                stat = item.stat()
                results.append({
                    "path": str(item),
                    "name": item.name,
                    "is_file": item.is_file(),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except (PermissionError, FileNotFoundError):
                continue
        
        return results

    def get_file_info(self, path: Union[str, Path]) -> dict:
        """Get detailed information about a file."""
        path = self._validate_path(path)
        stat = path.stat()
        
        return {
            "path": str(path),
            "name": path.name,
            "extension": path.suffix,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
        }

    # ==================== WRITE OPERATIONS ====================

    def create_file(
        self,
        path: Union[str, Path],
        content: str = "",
        overwrite: bool = False,
        encoding: str = "utf-8",
    ) -> bool:
        """
        Create a new file with content.
        
        Args:
            path: File path to create
            content: Initial content
            overwrite: Whether to overwrite existing file
            encoding: File encoding
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        backup_path = None
        
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {path}")
        
        if path.exists():
            backup_path = self._create_backup(path)
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            self._log_operation("create", str(path), True, f"Created with {len(content)} chars", backup_path)
            return True
        except Exception as e:
            self._log_operation("create", str(path), False, str(e))
            raise

    def write_file(
        self,
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
    ) -> bool:
        """
        Write content to a file (creates or overwrites).
        
        Args:
            path: File path
            content: Content to write
            encoding: File encoding
            
        Returns:
            True if successful
        """
        return self.create_file(path, content, overwrite=True, encoding=encoding)

    def append_to_file(
        self,
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
    ) -> bool:
        """
        Append content to an existing file.
        
        Args:
            path: File path
            content: Content to append
            encoding: File encoding
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        backup_path = self._create_backup(path)
        
        try:
            with open(path, "a", encoding=encoding) as f:
                f.write(content)
            self._log_operation("append", str(path), True, f"Appended {len(content)} chars", backup_path)
            return True
        except Exception as e:
            self._log_operation("append", str(path), False, str(e))
            raise

    def insert_at_line(
        self,
        path: Union[str, Path],
        line_number: int,
        content: str,
    ) -> bool:
        """
        Insert content at a specific line number.
        
        Args:
            path: File path
            line_number: Line number to insert at (1-indexed)
            content: Content to insert
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        backup_path = self._create_backup(path)
        
        try:
            lines = path.read_text().splitlines(keepends=True)
            insert_idx = max(0, min(line_number - 1, len(lines)))
            
            if not content.endswith("\n"):
                content += "\n"
            
            lines.insert(insert_idx, content)
            path.write_text("".join(lines))
            
            self._log_operation("insert", str(path), True, f"Inserted at line {line_number}", backup_path)
            return True
        except Exception as e:
            self._log_operation("insert", str(path), False, str(e))
            raise

    def replace_in_file(
        self,
        path: Union[str, Path],
        old_text: str,
        new_text: str,
        count: int = -1,
    ) -> int:
        """
        Replace text in a file.
        
        Args:
            path: File path
            old_text: Text to find
            new_text: Replacement text
            count: Max replacements (-1 for all)
            
        Returns:
            Number of replacements made
        """
        path = self._validate_path(path)
        backup_path = self._create_backup(path)
        
        try:
            content = path.read_text()
            
            if count == -1:
                new_content = content.replace(old_text, new_text)
                replacements = content.count(old_text)
            else:
                new_content = content.replace(old_text, new_text, count)
                replacements = min(count, content.count(old_text))
            
            path.write_text(new_content)
            
            self._log_operation(
                "replace", str(path), True,
                f"Made {replacements} replacement(s)", backup_path
            )
            return replacements
        except Exception as e:
            self._log_operation("replace", str(path), False, str(e))
            raise

    def replace_lines(
        self,
        path: Union[str, Path],
        start_line: int,
        end_line: int,
        new_content: str,
    ) -> bool:
        """
        Replace a range of lines with new content.
        
        Args:
            path: File path
            start_line: Starting line (1-indexed, inclusive)
            end_line: Ending line (inclusive)
            new_content: New content to insert
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        backup_path = self._create_backup(path)
        
        try:
            lines = path.read_text().splitlines(keepends=True)
            
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            new_lines = new_content.splitlines(keepends=True)
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            
            lines[start_idx:end_idx] = new_lines
            path.write_text("".join(lines))
            
            self._log_operation(
                "replace_lines", str(path), True,
                f"Replaced lines {start_line}-{end_line}", backup_path
            )
            return True
        except Exception as e:
            self._log_operation("replace_lines", str(path), False, str(e))
            raise

    # ==================== DELETE OPERATIONS ====================

    def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete a file.
        
        Args:
            path: File path to delete
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        backup_path = self._create_backup(path)
        
        try:
            path.unlink()
            self._log_operation("delete", str(path), True, "File deleted", backup_path)
            return True
        except Exception as e:
            self._log_operation("delete", str(path), False, str(e))
            raise

    def delete_directory(
        self,
        path: Union[str, Path],
        recursive: bool = False,
    ) -> bool:
        """
        Delete a directory.
        
        Args:
            path: Directory path
            recursive: Whether to delete contents
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        
        try:
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
            self._log_operation("delete_dir", str(path), True, "Directory deleted")
            return True
        except Exception as e:
            self._log_operation("delete_dir", str(path), False, str(e))
            raise

    def delete_lines(
        self,
        path: Union[str, Path],
        start_line: int,
        end_line: int,
    ) -> bool:
        """
        Delete a range of lines from a file.
        
        Args:
            path: File path
            start_line: Starting line (1-indexed)
            end_line: Ending line (inclusive)
            
        Returns:
            True if successful
        """
        return self.replace_lines(path, start_line, end_line, "")

    # ==================== MOVE/COPY OPERATIONS ====================

    def move_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
    ) -> bool:
        """
        Move or rename a file.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            True if successful
        """
        source = self._validate_path(source)
        destination = self._validate_path(destination)
        
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            self._log_operation("move", str(source), True, f"Moved to {destination}")
            return True
        except Exception as e:
            self._log_operation("move", str(source), False, str(e))
            raise

    def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
    ) -> bool:
        """
        Copy a file.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            True if successful
        """
        source = self._validate_path(source)
        destination = self._validate_path(destination)
        
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))
            self._log_operation("copy", str(source), True, f"Copied to {destination}")
            return True
        except Exception as e:
            self._log_operation("copy", str(source), False, str(e))
            raise

    def create_directory(self, path: Union[str, Path]) -> bool:
        """
        Create a directory (and parents if needed).
        
        Args:
            path: Directory path
            
        Returns:
            True if successful
        """
        path = self._validate_path(path)
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            self._log_operation("create_dir", str(path), True, "Directory created")
            return True
        except Exception as e:
            self._log_operation("create_dir", str(path), False, str(e))
            raise

    # ==================== DIFF & PATCH ====================

    def generate_diff(
        self,
        original: str,
        modified: str,
        filename: str = "file",
    ) -> str:
        """
        Generate a unified diff between two strings.
        
        Args:
            original: Original content
            modified: Modified content
            filename: Filename for diff header
            
        Returns:
            Unified diff string
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
        
        return "".join(diff)

    def compare_files(
        self,
        file1: Union[str, Path],
        file2: Union[str, Path],
    ) -> str:
        """
        Generate a diff between two files.
        
        Args:
            file1: First file path
            file2: Second file path
            
        Returns:
            Unified diff
        """
        content1 = self.read_file(file1)
        content2 = self.read_file(file2)
        
        return self.generate_diff(content1, content2, str(file1))

    # ==================== SEARCH ====================

    def search_files(
        self,
        directory: Union[str, Path] = ".",
        pattern: str = "*",
        text_pattern: Optional[str] = None,
        recursive: bool = True,
    ) -> list[dict]:
        """
        Search for files matching criteria.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for filenames
            text_pattern: Text pattern to search within files
            recursive: Whether to search recursively
            
        Returns:
            List of matching files with match info
        """
        directory = self._validate_path(directory)
        results = []
        
        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            match_info = {
                "path": str(file_path),
                "name": file_path.name,
                "matches": [],
            }
            
            if text_pattern:
                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        if text_pattern in line:
                            match_info["matches"].append({
                                "line": i,
                                "content": line.strip(),
                            })
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                if match_info["matches"]:
                    results.append(match_info)
            else:
                results.append(match_info)
        
        return results

    def grep(
        self,
        pattern: str,
        directory: Union[str, Path] = ".",
        file_pattern: str = "*",
    ) -> list[dict]:
        """
        Search for text pattern in files (grep-like).
        
        Args:
            pattern: Text pattern to search
            directory: Directory to search
            file_pattern: Glob pattern for files
            
        Returns:
            List of matches
        """
        return self.search_files(
            directory=directory,
            pattern=file_pattern,
            text_pattern=pattern,
            recursive=True,
        )

    # ==================== UNDO ====================

    def restore_backup(self, backup_path: Union[str, Path]) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Extract original filename
        name_parts = backup_path.name.rsplit(".", 2)
        if len(name_parts) >= 2:
            original_name = name_parts[0]
        else:
            original_name = backup_path.stem
        
        # Find original path in operation history
        original_path = None
        for op in reversed(self.operation_history):
            if op.backup_path == str(backup_path):
                original_path = op.path
                break
        
        if original_path:
            shutil.copy2(backup_path, original_path)
            self._log_operation("restore", original_path, True, f"Restored from {backup_path}")
            return True
        
        raise ValueError("Could not determine original path for backup")

    def get_operation_history(self) -> list[dict]:
        """Get history of file operations."""
        return [
            {
                "operation": op.operation,
                "path": op.path,
                "success": op.success,
                "message": op.message,
                "timestamp": op.timestamp.isoformat(),
                "backup_path": op.backup_path,
            }
            for op in self.operation_history
        ]

    def list_backups(self) -> list[str]:
        """List all backup files."""
        if not self.backup_dir.exists():
            return []
        return [str(f) for f in self.backup_dir.glob("*.bak")]
