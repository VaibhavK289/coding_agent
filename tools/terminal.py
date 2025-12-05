"""
Terminal Tools - Execute commands and interact with the system.
"""

import os
import subprocess
import shlex
import platform
from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    success: bool


class TerminalTools:
    """
    Terminal/shell execution tools for the AI agent.
    
    Features:
    - Execute shell commands
    - Run scripts
    - Manage processes
    - Environment handling
    """

    def __init__(
        self,
        working_directory: str = ".",
        shell: bool = True,
        timeout: int = 300,
    ):
        """
        Initialize terminal tools.
        
        Args:
            working_directory: Default working directory
            shell: Whether to use shell execution
            timeout: Default command timeout in seconds
        """
        self.working_directory = Path(working_directory).resolve()
        self.shell = shell
        self.timeout = timeout
        self.is_windows = platform.system() == "Windows"

    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[dict] = None,
        capture_output: bool = True,
    ) -> CommandResult:
        """
        Execute a shell command.
        
        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Command timeout
            env: Environment variables
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            CommandResult
        """
        cwd = Path(cwd).resolve() if cwd else self.working_directory
        timeout = timeout or self.timeout
        
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            result = subprocess.run(
                command,
                shell=self.shell,
                cwd=str(cwd),
                timeout=timeout,
                env=full_env,
                capture_output=capture_output,
                text=True,
            )
            
            return CommandResult(
                command=command,
                returncode=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                success=result.returncode == 0,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                success=False,
            )
        except Exception as e:
            return CommandResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=str(e),
                success=False,
            )

    def run_python(
        self,
        script: str,
        args: Optional[list[str]] = None,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Run a Python script.
        
        Args:
            script: Path to Python script
            args: Command line arguments
            cwd: Working directory
            
        Returns:
            CommandResult
        """
        cmd = f"python {script}"
        if args:
            cmd += " " + " ".join(args)
        return self.run_command(cmd, cwd=cwd)

    def run_python_code(
        self,
        code: str,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Run Python code directly.
        
        Args:
            code: Python code to execute
            cwd: Working directory
            
        Returns:
            CommandResult
        """
        # Escape for command line
        if self.is_windows:
            cmd = f'python -c "{code}"'
        else:
            cmd = f"python -c '{code}'"
        return self.run_command(cmd, cwd=cwd)

    def run_npm(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Run an npm command.
        
        Args:
            command: npm command (e.g., "install", "run build")
            cwd: Working directory
            
        Returns:
            CommandResult
        """
        return self.run_command(f"npm {command}", cwd=cwd)

    def run_git(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Run a git command.
        
        Args:
            command: git command (e.g., "status", "commit -m 'message'")
            cwd: Working directory
            
        Returns:
            CommandResult
        """
        return self.run_command(f"git {command}", cwd=cwd)

    def pip_install(
        self,
        packages: Union[str, list[str]],
        upgrade: bool = False,
    ) -> CommandResult:
        """
        Install Python packages with pip.
        
        Args:
            packages: Package(s) to install
            upgrade: Whether to upgrade existing packages
            
        Returns:
            CommandResult
        """
        if isinstance(packages, list):
            packages = " ".join(packages)
        
        cmd = f"pip install {packages}"
        if upgrade:
            cmd = f"pip install --upgrade {packages}"
        
        return self.run_command(cmd)

    def npm_install(
        self,
        packages: Optional[Union[str, list[str]]] = None,
        dev: bool = False,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Install npm packages.
        
        Args:
            packages: Package(s) to install (None for all from package.json)
            dev: Install as dev dependency
            cwd: Working directory
            
        Returns:
            CommandResult
        """
        if packages is None:
            return self.run_npm("install", cwd=cwd)
        
        if isinstance(packages, list):
            packages = " ".join(packages)
        
        flag = "--save-dev" if dev else "--save"
        return self.run_npm(f"install {flag} {packages}", cwd=cwd)

    def check_command_exists(self, command: str) -> bool:
        """
        Check if a command is available.
        
        Args:
            command: Command to check
            
        Returns:
            True if command exists
        """
        check_cmd = "where" if self.is_windows else "which"
        result = self.run_command(f"{check_cmd} {command}")
        return result.success

    def get_python_version(self) -> str:
        """Get Python version."""
        result = self.run_command("python --version")
        return result.stdout.strip() if result.success else "Unknown"

    def get_node_version(self) -> str:
        """Get Node.js version."""
        result = self.run_command("node --version")
        return result.stdout.strip() if result.success else "Not installed"

    def get_npm_version(self) -> str:
        """Get npm version."""
        result = self.run_command("npm --version")
        return result.stdout.strip() if result.success else "Not installed"

    def list_processes(self, filter_name: Optional[str] = None) -> str:
        """
        List running processes.
        
        Args:
            filter_name: Filter by process name
            
        Returns:
            Process list
        """
        if self.is_windows:
            cmd = "tasklist"
            if filter_name:
                cmd += f' /FI "IMAGENAME eq {filter_name}"'
        else:
            cmd = "ps aux"
            if filter_name:
                cmd += f" | grep {filter_name}"
        
        result = self.run_command(cmd)
        return result.stdout

    def kill_process(self, pid: int) -> CommandResult:
        """
        Kill a process by PID.
        
        Args:
            pid: Process ID
            
        Returns:
            CommandResult
        """
        if self.is_windows:
            cmd = f"taskkill /PID {pid} /F"
        else:
            cmd = f"kill -9 {pid}"
        
        return self.run_command(cmd)

    def get_environment(self) -> dict:
        """Get current environment variables."""
        return dict(os.environ)

    def set_environment(self, key: str, value: str):
        """Set an environment variable."""
        os.environ[key] = value

    def run_background(
        self,
        command: str,
        cwd: Optional[str] = None,
        log_file: Optional[str] = None,
    ) -> int:
        """
        Run a command in the background.
        
        Args:
            command: Command to run
            cwd: Working directory
            log_file: File to redirect output to
            
        Returns:
            Process ID
        """
        cwd = Path(cwd).resolve() if cwd else self.working_directory
        
        if log_file:
            if self.is_windows:
                command = f"{command} > {log_file} 2>&1"
            else:
                command = f"{command} > {log_file} 2>&1 &"
        
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL if not log_file else None,
            stderr=subprocess.DEVNULL if not log_file else None,
        )
        
        return process.pid
